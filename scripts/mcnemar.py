#!/usr/bin/env python3
"""
Recomputes every headline number in phase3/REPORT_phase3.md directly from
phase3/results_phase3.jsonl, plus McNemar's exact test on the paired
outcomes (same prompt, same instant, direct vs gateway) - the significance
test the report itself does not compute. No dependencies beyond the
standard library; run with any Python 3.

Usage:
    python3 scripts/mcnemar.py phase3/results_phase3.jsonl
"""
import json
import sys
from math import comb


def exact_binom_two_sided(k, n, p=0.5):
    """Two-sided exact binomial test p-value: sum of P(X=i) over every
    outcome at least as extreme (probability <= observed), the same
    definition scipy.stats.binomtest and R's binom.test use for McNemar's
    exact test on discordant pairs."""
    if n == 0:
        return float("nan")
    probs = [comb(n, i) * (p**i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
    pk = probs[k]
    eps = 1e-12
    return sum(pr for pr in probs if pr <= pk + eps)


def analyze(records, label):
    pairs = {}
    for r in records:
        pairs.setdefault(r["pair_seq"], {})[r["path"]] = r["success"]

    both_ok = both_fail = 0
    saved = gateway_only_failed = 0  # b, c in McNemar's 2x2 table
    n = 0
    for legs in pairs.values():
        if "direct" not in legs or "gateway" not in legs:
            continue
        n += 1
        d, g = legs["direct"], legs["gateway"]
        if d and g:
            both_ok += 1
        elif not d and not g:
            both_fail += 1
        elif not d and g:
            saved += 1
        else:
            gateway_only_failed += 1

    direct_fail = sum(1 for legs in pairs.values() if legs.get("direct") is False)
    gateway_fail = sum(1 for legs in pairs.values() if legs.get("gateway") is False)
    discordant = saved + gateway_only_failed
    k = min(saved, gateway_only_failed)
    p = exact_binom_two_sided(k, discordant) if discordant else float("nan")

    print(f"=== {label} ===")
    print(f"pairs: {n}")
    print(f"direct fail:  {direct_fail}/{n} ({100*direct_fail/n:.1f}%)")
    print(f"gateway fail: {gateway_fail}/{n} ({100*gateway_fail/n:.1f}%)")
    print(f"both ok={both_ok}  both fail={both_fail}  "
          f"requests saved (b)={saved}  gateway-only-failed (c)={gateway_only_failed}")
    if discordant:
        print(f"McNemar's exact test: n_discordant={discordant}, two-sided p={p:.4g}")
    else:
        print("no discordant pairs - McNemar's test is undefined")
    print()


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    records = []
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    analyze(records, "Combined (Standard + Super Deal)")
    analyze([r for r in records if r["line"] == "standard"], "Standard only")
    analyze([r for r in records if r["line"] == "super deal"], "Super Deal only")


if __name__ == "__main__":
    main()
