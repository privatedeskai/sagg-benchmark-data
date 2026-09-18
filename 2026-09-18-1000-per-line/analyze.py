#!/usr/bin/env python3
"""Recompute every number in this folder's README directly from the raw
JSONL - stdlib only, same "reproduce it yourself" principle as the rest
of this repo.

Each line (Standard/Super Deal) is split across 3 window files (window1,
window2, window3) - three separate, non-overlapping clean test runs that
combine to n=1,000 per line. This script pools all three windows for a
line together before computing percentiles (not an average of three
separate percentile sets, which would not be the correct pooled figure).

Usage:
    python3 analyze.py results_standard_window1.jsonl results_standard_window2.jsonl results_standard_window3.jsonl
    python3 analyze.py results_superdeal_window1.jsonl results_superdeal_window2.jsonl results_superdeal_window3.jsonl
"""
import json
import sys
from collections import defaultdict


def percentile(sorted_vals, p):
    """Nearest-rank by floor index, no interpolation - matches the exact
    method used to compute the numbers published on /benchmarks, so this
    script reproduces them exactly rather than a slightly different (but
    also valid) interpolated percentile."""
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

    # Only the "gateway" path records count toward n - this dataset (unlike
    # phase3/2026-09-12-postfix) has no working direct-provider comparison
    # leg configured, so "direct" records in these files (present because
    # the bench tool always attempts both) are not part of the headline
    # numbers; see this folder's README for why.
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
