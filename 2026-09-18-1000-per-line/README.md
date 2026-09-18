# 2026-09-18 update: 1,000 requests per line

**The current, largest headline figure - not a replacement for `phase3/`
or `2026-09-12-postfix/` above.** Both earlier eras are kept in this repo
unmodified; this folder is the current baseline. Real reliability fixes
landed in the gateway between the 2026-09-12 data and this one: connection
pooling (`MaxIdleConnsPerHost`) was fixed on both the streaming and
non-streaming HTTP transports (only streaming had it before), the Tier1
provider for both pricing lines recovered from an unrelated upstream
outage and was re-verified live, and an alert-escalation race in the
internal monitoring platform was fixed - none of these change how a
request is served, but the Tier1 recovery specifically changed which
provider serves the large majority of traffic, which is why this update
exists.

## What's different about this measurement

- **No paired direct-provider comparison leg.** Unlike `phase3/` (paired
  direct-vs-gateway, McNemar's test) and `2026-09-12-postfix/` (4
  concurrent legs including 3 direct provider calls), this data measures
  the gateway's own end-to-end reliability, latency, and tier routing
  only - the direct-comparison credentials were not part of this
  particular test run. The raw JSONL files still contain a `"path":
  "direct"` record per round (the bench tool always attempts both), but
  those direct legs failed on missing/invalid credentials (`auth_error`)
  in every case and are excluded from every number in this README and on
  the live page - `analyze.py` filters to `"path": "gateway"` only, not a
  silent omission.
- **Three separate, non-overlapping clean windows, not one continuous
  run** - see below. Each window individually satisfies two conditions:
  the connection-pooling fix and the Tier1 provider recovery were both
  already live, and the provider account's balance was confirmed healthy
  throughout (an earlier window that does NOT meet this bar - overlapping
  a real, disclosed balance-depletion incident - exists in this session's
  own internal records and was deliberately excluded, not blended in, to
  avoid mixing data from different operating conditions).
- **A dynamic per-request SLA** (`15s + max_tokens / 8.92 tokens/sec`,
  the same empirically-derived formula `2026-09-12-postfix/` introduced),
  not a flat cutoff.

## Windows

| Window | Line | n | Period (UTC) | Origin |
|---|---|---|---|---|
| 1 | Standard | 150 | 2026-09-16 21:08:45 - 21:20:22 | local test machine |
| 1 | Super Deal | 150 | 2026-09-16 21:20:38 - 21:25:36 | local test machine |
| 2 | Standard | 500 | 2026-09-17 19:05:07 - 20:52:18 | VPS (same host as the gateway) |
| 2 | Super Deal | 500 | 2026-09-17 20:52:18 - 22:32:35 | VPS |
| 3 | Standard | 350 | 2026-09-18 08:14:39 - 09:20:21 | VPS |
| 3 | Super Deal | 350 | 2026-09-18 09:20:21 - 10:37:19 | VPS |

**Disclosed nuance**: window 1 ran from a different network origin (a
local machine, not the VPS the gateway itself runs on) than windows 2-3.
This cannot affect success/failure or which tier served a request - both
are purely server-side facts, verified against the gateway's own
production logs at the time - but plausibly explains a modest amount of
the difference between window 1's own raw TTFT figures and the other two
windows' (window 1 in isolation: Standard TTFT median 283ms; windows 2+3
combined: closer to 190-200ms), folded into the combined percentiles
below rather than reported separately.

**Why window 1's tier attribution can't be independently re-verified from
this repo's raw files**: the per-request `provider`/`tier` breakdown for
window 1 was computed live against the gateway's own production logs at
the time (2026-09-16), which have since rotated out (the gateway process
was recreated for later, unrelated deploys) - the count is carried
forward from that contemporaneous measurement (137/150 Standard,
150/150 Super Deal via the Primary tier), not recomputed from this
folder's JSONL, which only has the bench tool's own client-side
success/TTFT view, not the tier that served each request. Windows 2 and 3
were cross-referenced against still-available production logs and are
independently reproducible.

## Results (pooled across all three windows per line)

| Line | n | Success | Fail % | TTFT mean | TTFT median | TTFT p90 | TTFT p95 |
|---|---|---|---|---|---|---|---|
| Standard | 1,000 | 1,000 (100.0%) | 0.0% | 644ms | 197ms | 776ms | 1821ms |
| Super Deal | 1,000 | 989 (98.9%) | 1.1% | 416ms | 216ms | 1154ms | 1568ms |

Super Deal's 11 failures: 10 `empty_body` (every tier attempted, none
delivered content before the request's own SLA), 1 `timeout`.

## Which tier served the request

| Line | Primary (`joingonka-deepseek`) | Backup |
|---|---|---|
| Standard | 945/1,000 (94.5%) | `eterial-deepseek` 46 (4.6%), `deepinfra-deepseek` 9 (0.9%) |
| Super Deal | 914/989 (92.4%) | `gonkaapiorg-deepseek` 75 (7.6%) |

Computed by matching each successful request's `sagg_request_id` against
the gateway's own structured production logs (`"message":"Stream
billed"`) for windows 2-3; window 1's figures are the contemporaneous
measurement described above.

## Reproducing this

```
python3 analyze.py results_standard_window1.jsonl results_standard_window2.jsonl results_standard_window3.jsonl
python3 analyze.py results_superdeal_window1.jsonl results_superdeal_window2.jsonl results_superdeal_window3.jsonl
```

Stdlib only, no dependencies. Reproduces the success/fail/TTFT numbers in
this README exactly (same percentile method: nearest-rank by floor index,
not interpolated). The tier-attribution table above is not reproducible
from this script alone (it requires the production log cross-reference
described above, not present in these client-side JSONL files) - it is
reported as a measurement, not a script output.

## What this data does NOT claim

Same principles as `METHODOLOGY.md` one level up: not a claim about
response quality, not a permanent verdict on any provider (Gonka-network
reliability moves on a timescale of minutes), and these absolute numbers
are specific to this SLA, this prompt mix, and these three windows - not
a universal uptime figure. This measurement also does not include a
burst/concurrent-load scenario - see this session's own internal records
for that (a real, disclosed, and materially different characteristic:
the Primary tier's own share of traffic drops substantially under a
genuine concurrent burst, even though overall cascade success stays
high) - not included on the public page because it does not reflect
typical realistic client traffic, per this repo's own "real-content-only"
principle.
