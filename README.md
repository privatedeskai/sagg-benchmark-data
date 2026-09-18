# SAGG gateway reliability benchmarks

Raw data, methodology, and reproduction scripts behind two real benchmark
campaigns run against [SAGG](https://api.privatedeskai.com), an LLM
inference gateway that fronts several providers on the
[Gonka](https://gonka.ai) decentralized inference network plus one
centralized fallback (DeepInfra), with automatic failover between them.

Everything in this repo is real, measured data - no numbers here are
projected, simulated, or smoothed. Where a result was noisy or a finding
was unflattering (a provider's own failure rate, a gateway-only loss), it
is reported as measured.

**Update, 2026-09-18 (current headline figure)**: the largest sample to
date - **1,000 real sequential requests per line**, measured after this
session's own connection-pooling fix and a Tier1 provider recovery, is in
[`2026-09-18-1000-per-line/`](2026-09-18-1000-per-line/): **Standard
1,000/1,000 (100.0%)**, **Super Deal 989/1,000 (98.9%)**, median
time-to-first-token 197ms/216ms. This is now the number quoted first on
the public `/benchmarks` page. See that folder's own README for the full
methodology (three separate clean-condition windows pooled together, no
paired direct-comparison leg this time, and an honestly disclosed
network-origin nuance for one of the three windows).

**Update, 2026-09-12**: several real reliability fixes landed in the
gateway since the campaigns below were run (a per-request dynamic timeout,
a cascade-order fix, improved stream-completion logging). A new,
separate measurement taken after those fixes - across both pricing
lines and light/heavy prompt loads - is in
[`2026-09-12-postfix/`](2026-09-12-postfix/): **~98% success (652/667)**,
median time-to-first-token ~10-13ms (light) to ~240-280ms (heavy). This
does not replace the numbers below - both are kept, dated, so nothing is
quietly swapped out; see that folder's own README for the full
methodology difference and two disclosed findings from that run.

## Headline result (Phase 3, 2026-09-03/05 - historical baseline)

Over 1,440 paired requests (same prompt, same instant, one request sent
directly to `proxygonka-deepseek`, one sent through the SAGG gateway),
the gateway's automatic failover measurably reduced end-to-end failures:

| | direct failure rate | gateway failure rate | requests saved | McNemar's exact p |
|---|---|---|---|---|
| Combined | 522/1440 (36.2%) | 393/1440 (27.3%) | +177 (net +129 after 48 gateway-only losses) | 1.6e-12 |
| Standard line | 254/720 (35.3%) | 152/720 (21.1%) | +126 | 8.8e-13 |
| Super Deal line | 268/720 (37.2%) | 241/720 (33.5%) | +51 | 0.0024 |

"Requests saved" = direct failed, gateway succeeded, same prompt, same
instant. All three splits are statistically significant, but Standard's
benefit is much larger than Super Deal's - see `phase3/REPORT_phase3.md`
for the full incident-by-incident log and why (Super Deal's own backup
tier is measurably less reliable than Standard's).

A separate, smaller campaign (`provider_benchmark/`) measured each of the
four underlying providers directly (25 requests each) and caught all
three Gonka-network brokers degraded simultaneously in the same test
window - see below.

## What's in this repo

- **`2026-09-18-1000-per-line/`** - the current headline figure: 1,000
  requests per line pooled from three separate clean-condition windows,
  taken after the connection-pooling fix and a Tier1 provider recovery,
  with a dependency-free reproduction script. Read this folder's own
  README first - it has no paired direct-comparison leg, unlike the two
  entries below.
- **`2026-09-12-postfix/`** - the prior baseline: 5 test runs (Standard
  + Super Deal, light + heavy prompt loads, plus a direct-provider
  snapshot) taken after this session's own reliability fixes, with a
  dependency-free reproduction script and two disclosed findings from
  that run. Read this folder's own README before comparing its numbers
  to Phase 3 below - different date, different code, different
  methodology (unpaired 4-concurrent-legs, not paired direct-vs-gateway).
- **`phase3/`** - the large campaign: 1,440 paired requests (Standard +
  Super Deal, alternating), 3 days, `results_phase3.jsonl` (raw,
  request-level records) and the full generated report with a per-pair
  incident log.
- **`provider_benchmark/`** - 100 direct (non-gateway) requests, 25 per
  provider (`proxygonka-deepseek`, `gonkaapiorg-deepseek`,
  `eterial-deepseek`, `deepinfra-deepseek`), with latency percentiles and
  failure breakdowns per provider.
- **`traces/`** - four real, raw JSON traces from SAGG's own per-request
  tracing tool, each showing the exact chronology (timestamp + outcome)
  of every tier attempted for one request. `trace_full_cascade_*.json` is
  the most interesting one: a single real production request where Tier1
  timed out, Tier2 ALSO timed out, and Tier3 finally succeeded - captured
  from real, unforced traffic, not staged.
- **`scripts/mcnemar.py`** - recomputes every number above (and the
  significance test) directly from the raw JSONL. Stdlib only.
- **`METHODOLOGY.md`** - what counts as a failure, how pairing works, and
  how to independently re-run the analysis.

## Reproduce it yourself

```bash
python3 scripts/mcnemar.py phase3/results_phase3.jsonl
```

No dependencies, no accounts, no API keys needed - it's pure arithmetic
over the raw JSONL. If you get different numbers than the table above,
something is wrong (with this repo, or tell us and we'll look).

## Dates

- Phase 3 campaign: 2026-09-03 15:49 UTC - 2026-09-05 03:18 UTC.
- Provider benchmark: 2026-09-05 (~12:00-12:35 UTC).
- Post-fix update: 2026-09-12 (~06:41 UTC - 20:12 UTC, five separate runs - see `2026-09-12-postfix/README.md` for exact windows per file).

Reliability on a decentralized inference network moves fast - see
METHODOLOGY.md's "a snapshot, not a constant" note before treating any
single number here as a permanent fact about a provider.

## License

Data and scripts in this repo: CC0 (public domain) / MIT, whichever is
more useful to you. Attribution appreciated but not required.
