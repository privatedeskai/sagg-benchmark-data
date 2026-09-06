# Per-provider direct benchmark (100 requests, 2026-09-05)

25 direct (non-gateway) requests per provider, real base URL/key/model
for each provider, same 9-prompt bank and 15s SLA as the Phase 3
campaign (see `../METHODOLOGY.md`). Full raw records in
`results_provider_benchmark.jsonl`; summary statistics in
`provider_benchmark_summary.json`.

| Provider | Attempts | Success | Failures | Fail % | Fail reasons | Latency p50 (ms) | min (ms) | max (ms) |
|---|---|---|---|---|---|---|---|---|
| `proxygonka-deepseek` | 25 | 8 | 17 | 68.0% | timeout: 17 | 71.5 | 7 | 8706 |
| `gonkaapiorg-deepseek` | 25 | 16 | 9 | 36.0% | timeout: 9 | 726.5 | 496 | 13383 |
| `eterial-deepseek` | 25 | 13 | 12 | 48.0% | timeout: 12 | 74 | 55 | 2083 |
| `deepinfra-deepseek` | 25 | 24 | 1 | 4.0% | timeout: 1 | 5648.5 | 492 | 12782 |

TTFT (time-to-first-token) p50, success-only: proxygonka 64ms,
gonkaapiorg 698.5ms, eterial 49ms, deepinfra 432.5ms.

## Headline finding

All three Gonka-network brokers (`proxygonka-deepseek`,
`gonkaapiorg-deepseek`, `eterial-deepseek`) showed elevated failure
rates (36-68%) in this same test window - a real, currently-occurring,
network-wide condition, not one broker having an isolated bad day.
`deepinfra-deepseek`, the one non-Gonka provider in this set, stayed at
96% success. This is exactly the failure mode a gateway with a
non-Gonka fallback tier is designed to survive - see the "full cascade"
trace in `../traces/` for a real example of all three Gonka tiers
failing in sequence on one request, with DeepInfra ultimately serving it.

## Gateway-vs-direct, same window

A supplementary check - 16 real gateway calls made in roughly the same
window as this benchmark - found all 16 succeeding directly on Tier1
(`proxygonka-deepseek`), zero failovers needed. This is a real,
honestly-reported contrast with the 68% direct-path failure rate
measured only minutes earlier on the same provider: see
`../METHODOLOGY.md`'s "a snapshot, not a constant" section. Provider
health on this network moves fast; a single benchmark window describes
a moment, not a fixed state.

## Response content was spot-checked, not assumed

One successful sample per provider was read back to confirm it was
coherent, on-topic model output (not an empty-but-200 false positive) -
e.g. `proxygonka-deepseek` answered a states-of-matter question
correctly, `gonkaapiorg-deepseek` produced real working Go code,
`eterial-deepseek` correctly named Canberra as Australia's capital, and
`deepinfra-deepseek` correctly ranked support-ticket complaints by
severity.
