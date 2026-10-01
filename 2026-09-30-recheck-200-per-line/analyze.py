#!/usr/bin/env python3
"""Recompute every number in this folder's README directly from the raw
JSONL - stdlib only, same "reproduce it yourself" principle as the rest
of this repo.

This is a single clean window per line (not pooled across multiple
windows like 2026-09-18-1000-per-line/) - a short recheck, not a new
large-sample measurement.

Usage:
    python3 analyze.py results_standard.jsonl
    python3 analyze.py results_superdeal.jsonl
"""
import json
import sys
from collections import defaultdict


def percentile(sorted_vals, p):
    """Nearest-rank by floor index, no interpolation - matches the exact
    method used to compute the numbers published on /benchmarks and in
    2026-09-18-1000-per-line/, so this script reproduces them exactly."""
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    return sorted_vals[min(int(p * (n - 1)), n - 1)]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    records = []
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    # Only "gateway" path records count - this dataset has no working
    # direct-provider comparison leg configured, same as
    # 2026-09-18-1000-per-line/ (see that folder's own README for why).
    gw = [r for r in records if r.get("path") == "gateway"]
    n = len(gw)
    fails = [r for r in gw if not r["success"]]
    ttfts = sorted(r["ttft_ms"] for r in gw if r["success"] and r.get("ttft_ms"))
    classes = defaultdict(int)
    for r in fails:
        classes[r.get("error_class") or f"http_{r['http_status']}"] += 1

    print(f"n={n}  fails={len(fails)} ({100.0 * len(fails) / n:.1f}%)  success={n - len(fails)} ({100.0 * (n - len(fails)) / n:.1f}%)")
    if ttfts:
        print(
            f"TTFT ms (success only, n={len(ttfts)}): "
            f"mean={sum(ttfts) / len(ttfts):.0f} "
            f"median={percentile(ttfts, 0.5):.0f} "
            f"p90={percentile(ttfts, 0.9):.0f} "
            f"p95={percentile(ttfts, 0.95):.0f} "
            f"max={max(ttfts):.0f}"
        )
    if classes:
        print(f"fail breakdown: {dict(classes)}")


if __name__ == "__main__":
    main()
