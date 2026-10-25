#!/usr/bin/env python3
"""analyze.py - recomputes the headline figures of the R1 24-hour run from main_requests.csv (dependency-free, standard library only).
usage: python3 analyze.py [main_requests.csv]   ->  per line: requests, served (Wilson 95 %), first-text median / p95 / p99 (an ESTIMATE from one daily cycle), per class.
Definitions: served = HTTP 200 with a complete answer (column `served`); first text = `ttft_ms` of served streaming requests. Percentiles by linear interpolation."""
import csv, math, sys, collections

path = sys.argv[1] if len(sys.argv) > 1 else "main_requests.csv"
rows = list(csv.DictReader(open(path, encoding="utf-8")))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def pct(vals, q):
    s = sorted(vals)
    k = (len(s) - 1) * q
    f, c = math.floor(k), math.ceil(k)
    return s[int(k)] if f == c else s[f] + (s[c] - s[f]) * (k - f)


for line in ("standard", "super deal"):
    L = [r for r in rows if r["line"] == line and not r["ext_incident"]]
    k = sum(r["served"] == "1" for r in L)
    lo, hi = wilson(k, len(L))
    ft = [float(r["ttft_ms"]) for r in L if r["stream"] == "1" and r["served"] == "1" and r["ttft_ms"]]
    print("%s: %d requests, served %d (%.3f %%, Wilson 95 %% %.3f-%.3f), first text median %.0f ms, p95 %.0f ms, p99 (estimate) %.0f ms, n=%d" % (
        line, len(L), k, 100.0 * k / len(L), 100 * lo, 100 * hi, pct(ft, .5), pct(ft, .95), pct(ft, .99), len(ft)))
    by = collections.defaultdict(list)
    for r in L:
        by[r["cls"]].append(r)
    for c, rs in sorted(by.items()):
        kk = sum(r["served"] == "1" for r in rs)
        print("   %-16s %5d requests, served %5d (%.2f %%)" % (c, len(rs), kk, 100.0 * kk / len(rs)))
