#!/usr/bin/env python3
"""Recompute every number in this folder's README directly from the raw
JSONL - stdlib only, same "reproduce it yourself" principle as
scripts/mcnemar.py one level up.

This dataset is NOT paired (unlike phase3/results_phase3.jsonl) - each
round fires the gateway leg plus its underlying direct provider legs
concurrently against the same prompt, but there is no "direct-vs-gateway
matched pair" structure to run McNemar's test on. This script just does
straightforward per-leg counting: n, failures, fail %, and TTFT
percentiles over successful requests.

Usage:
    python3 analyze.py results_standard_light.jsonl
    python3 analyze.py results_superdeal_heavy.jsonl
"""
import json
import sys
from collections import defaultdict


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    by_leg = defaultdict(list)
    with open(sys.argv[1], encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                by_leg[json.loads(line)["line"]].append(json.loads(line))

    for leg, recs in by_leg.items():
        n = len(recs)
        fails = [r for r in recs if not r["success"]]
        ttfts = sorted(r["ttft_ms"] for r in recs if r["success"])
        classes = defaultdict(int)
        for r in fails:
            classes[r.get("error_class") or f"http_{r['http_status']}"] += 1

        print(f"=== {leg} ===")
        print(f"n={n}  fails={len(fails)} ({100.0 * len(fails) / n:.1f}%)")
        if ttfts:
            print(
                f"TTFT ms (success only): "
                f"mean={sum(ttfts) / len(ttfts):.0f} "
                f"median={percentile(ttfts, 0.5):.0f} "
                f"p90={percentile(ttfts, 0.9):.0f}"
            )
        if classes:
            print(f"fail breakdown: {dict(classes)}")
        print()


if __name__ == "__main__":
    main()
