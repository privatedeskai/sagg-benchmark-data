# 2026-09-12 post-fix update

**This is a separate, later measurement - not a replacement for `phase3/`
or `provider_benchmark/` above.** Several real reliability fixes landed
in the gateway between the original Phase 3 campaign (2026-09-03/05) and
this data: a per-request dynamic SLA timeout (scaled to `max_tokens`,
replacing a flat 15-second ceiling), a cascade-order fix, and improved
stream-completion logging. The numbers below describe the gateway's
behavior *after* those fixes, on a *different day*, using a *different
methodology* (see below) - they are not a like-for-like "before/after"
delta on the same measurement. Both eras are kept in this repo so nothing
is quietly replaced; read the top-level README's own headline numbers as
the historical baseline, and this folder as the current one.

## Methodology difference from Phase 3

Phase 3 pairs one direct request with one gateway request, same prompt,
same instant. This data instead fires **4 concurrent legs per round**:
the gateway (through its real cascade) plus each of its 3 underlying
providers, all against the same prompt at the same instant - so it
measures both the gateway's own end-to-end reliability AND each
individual provider's standalone reliability in the same window, rather
than only the gateway-vs-one-provider comparison Phase 3 used. There is
no paired-request structure here, so McNemar's test (used in
`phase3/`) does not apply - `analyze.py` in this folder does simple
per-leg failure-rate and TTFT-percentile counting instead. Failure
criteria are otherwise the same as `METHODOLOGY.md`'s definition
(non-2xx, connection error, or a stream that started and stalled) -
except the SLA cutoff for "stalled" is now `15s + max_tokens / 8.92
tokens/sec` (empirically-derived minimum real generation speed) instead
of a flat 15s, since the flat cutoff was producing false "timeouts" on
long, still-in-progress generations.

## What's in this folder

- `results_standard_light.jsonl` - 200 rounds, Standard line (`proxygonka-deepseek` -> `eterial-deepseek` -> `deepinfra-deepseek`), the default 9-prompt bank (varied per request, see cache-safety note below), 2026-09-12 06:53:16-07:44:49 UTC.
- `results_standard_heavy.jsonl` - 180 rounds, Standard line, a heavier prompt set (long multi-step reasoning, long-context document summarization, code generation + a short-QA control), 2026-09-12 16:16:46-17:22:36 UTC.
- `results_superdeal_light.jsonl` - 180 rounds, Super Deal line (`proxygonka-deepseek` -> `gonkaapiorg-deepseek` -> `eterial-deepseek`, a different provider set/order than Standard), same light prompt bank, 2026-09-12 18:23:23-18:29 UTC.
- `results_superdeal_heavy.jsonl` - 180 rounds, Super Deal line, same heavy prompt set, 2026-09-12 18:57:01-20:12:27 UTC.
- `results_gonkaapiorg_direct.jsonl` - 200 direct (non-gateway) requests to `gonkaapiorg-deepseek` alone, 2026-09-12 06:41:58-06:51:52 UTC (a separate, ~10-20 minute earlier window than the other four files - see caveat below).
- `analyze.py` - dependency-free reproduction script; `python3 analyze.py <file>` prints n/fail%/TTFT percentiles per leg.

## Cache-safety

Both prompt banks used per-request content variation (randomized
subsets/reordering/openings, not a static fixed string repeated every
round) specifically so no request shares an identical prompt prefix with
another - relevant because DeepSeek-family providers offer a
meaningfully discounted price for cached-prefix matches, and a benchmark
that accidentally hit that path on every round would not reflect a real
customer's typical traffic pattern.

## Results

| Line | Workload | Requests | Fail % | TTFT median | TTFT p90 |
|---|---|---|---|---|---|
| Standard | Light | 200 | 3.0% (1.0% excl. artifact, see below) | 13ms | 1406ms |
| Standard | Heavy | 107 usable&sup1; | 4.7% | 241ms | 1958ms |
| Super Deal | Light | 180 | 0.0% | 11ms | 15ms |
| Super Deal | Heavy | 180 | 4.4% | 278ms | 2629ms |

&sup1;Only 107 of the 180 attempted Standard-heavy requests are usable -
73 were rejected pre-cascade by SAGG's own quota check because the test
account ran low on quota partway through this specific run (heavy
prompts bill more per request than light ones). This is a **test-account
artifact, not a gateway or provider failure** - it is still present in
`results_standard_heavy.jsonl` (`quota_exceeded`, easy to filter), kept
rather than removed from the raw file so the full, real record is
available.

**Combined across all four gateway-leg rows: 652/667 successful (97.8%)**,
after excluding one disclosed artifact (below). Raw, uncorrected:
648/667 (97.2%).

Direct-provider snapshot, same day:

| Provider | Requests | Fail % | TTFT p50 |
|---|---|---|---|
| `proxygonka-deepseek` | 200 | 7.5%&sup2; | 8ms |
| `eterial-deepseek` | 200 | 5.5% | 79ms |
| `gonkaapiorg-deepseek` | 200 | 0.5%&sup3; | 700ms |
| `deepinfra-deepseek` | 200 | 0.0% | 427ms |

&sup2;10 of these 15 failures are `rate_limited` - see the self-collision
finding directly below; likely inflates this specific number above its
true baseline for this window. &sup3;`gonkaapiorg-deepseek`'s own window
(`results_gonkaapiorg_direct.jsonl`) ran ~10-20 minutes before the other
three started - not the same concurrent snapshot the Standard/
proxygonka/eterial/deepinfra rows share with each other.

## Two real findings, disclosed in full rather than smoothed over

**1. A self-inflicted rate-limit collision, not a production signal.**
4 of Standard-light's 6 raw failures, and 10 of proxygonka-deepseek's own
15 direct failures, are `rate_limited` and cluster in the first few
minutes of their run - this coincides with this session's own continuous
reliability monitor (a separate, unrelated background process hitting
the same real provider API keys) starting a scheduled cycle at almost
exactly the same moment. This is two of our own test/monitoring
processes competing for the same real provider-side rate limit, not
something a real customer would ever experience - excluding it is the
source of the "1.0%"/"97.8%" corrected figures above. The raw,
uncorrected numbers are shown too, not hidden.

**2. A genuine 3-tier cascade exhaustion under heavy Super Deal load,
also traced to the same root cause in a different shape.** 4 of Super
Deal-heavy's 8 gateway failures are `all_providers_down` - all 3 tiers
failed in the same round. Investigated directly: 3 of these 4 rounds show
`proxygonka-deepseek` AND `gonkaapiorg-deepseek` (Super Deal's own real
Gonka-network Tier1/Tier2) hit provider-side `429 rate_limited`
simultaneously, and all 4 fall inside a window overlapping the same
continuous monitor's own next scheduled cycle - the identical
shared-provider-API-key contention as finding 1, just manifesting as a
full-cascade failure this time instead of a single-leg one. Not a
Super-Deal-specific reliability defect; a real operational interaction
between this project's own tooling, disclosed because it materially
explains this run's most distinctive failure mode.

## Reproduce it yourself

```bash
python3 analyze.py results_standard_light.jsonl
python3 analyze.py results_superdeal_heavy.jsonl
```

No dependencies. If you get different numbers than the tables above,
something is wrong (with this repo, or tell us and we'll look).
