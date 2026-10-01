# 2026-09-30 recheck: 200 requests per line, two weeks after the 1,000/line baseline

**This is a short confirmation check, not a new large-sample measurement.** Its purpose was narrow: verify the [`2026-09-18-1000-per-line/`](../2026-09-18-1000-per-line/) baseline (100.0%/98.9%) still held two weeks later, given real changes on the Gonka network in the interim (new models observed: GLM-5.3-Flash, MiniMax-M2.7). At n=200/line this does not carry the same statistical weight as the 1,000-request baseline - read it as "still consistent with," not as a replacement measurement.

## Methodology differences from 2026-09-18-1000-per-line/

- **A different, heavier prompt bank** (`prompts_v4_balanced.json`: 60 prompts, evenly split across `short_qa` (max_tokens=150), `long_context` (max_tokens=500, 433-728 character inputs), and `code_gen` (max_tokens=700) - versus the original baseline's `prompts.json`, 9 prompts, all `short_qa`). This was a deliberate choice for this check, not an oversight - but it means **TTFT is not directly comparable** to the 2026-09-18 figures: 2/3 of these requests are genuinely heavier tasks, which raises TTFT independent of any provider health change. Success rate and tier-attribution comparisons remain valid (those are purely server-side facts, unaffected by prompt mix).
- **A real test-infrastructure hiccup, disclosed rather than hidden**: the first attempt at the Standard leg hit `HTTP 402 quota_exceeded` on all 200 requests - an internal SAGG test account had drained its own prepaid balance after accumulating real usage across prior test sessions, unrelated to this check or to the gateway's actual behavior. The architect topped up the test account and Standard was cleanly rerun; `results_standard.jsonl` in this folder is that clean rerun, not the quota-blocked attempt (which is not included here, since it measured nothing about the gateway).

## Results

| Line | n | Success | Fail % | TTFT mean | TTFT median | TTFT p95 | TTFT max |
|---|---|---|---|---|---|---|---|
| Standard | 200 | 199 (99.5%) | 0.5% | 2727ms | 375ms | 14942ms | 24005ms |
| Super Deal | 200 | 198 (99.0%) | 1.0% | 1061ms | 488ms | 3852ms | 12262ms |

Both success rates are consistent with the 2026-09-18 baseline (100.0%/98.9%) - the headline reliability finding holds two weeks later.

## Which tier served the request

| Line | Primary (`joingonka-deepseek`) | Backup | vs. 2026-09-18 baseline |
|---|---|---|---|
| Standard | 160/199 (**80.4%**) | `deepinfra-deepseek` 27, `eterial-deepseek` 12 | down from 94.5% |
| Super Deal | 181/198 (91.4%) | `gonkaapiorg-deepseek` 16, `eterial-deepseek` 1 | close to 92.4% |

**Honest finding, not smoothed over**: Standard's Primary-tier share dropped meaningfully from the 2026-09-18 baseline. Confirmed via direct production-log inspection (not inferred from the JSONL alone - see the caveat below) - 78 occurrences of `"timeout awaiting response headers"` from `joingonka-deepseek` in this window (~39 unique affected requests out of 200, matching the gap in Tier1 share almost exactly). This is a real, if not severe, connection-level degradation specific to `joingonka` on the Standard line that day - overall success stayed high because the cascade's backup tiers absorbed it correctly, exactly as designed. Super Deal did not show the same drop in the same window.

As computed via direct inspection, same production environment, so not independently reproducible from this folder's two JSONL files alone (which only have the bench client's own success/TTFT view, not which tier served each request) - carried forward from that live, contemporaneous measurement, same disclosed-methodology-limit as `2026-09-18-1000-per-line/`'s own window-1 tier figures.

## Reproducing the success/TTFT numbers

```
python3 analyze.py results_standard.jsonl
python3 analyze.py results_superdeal.jsonl
```

Stdlib only, no dependencies. Reproduces the success/fail/TTFT numbers in this README exactly (same percentile method - nearest-rank by floor index - as `2026-09-18-1000-per-line/`). The tier-attribution table is not reproducible from this script alone, per the note above.

## What this data does NOT claim

Same principles as `METHODOLOGY.md` and `2026-09-18-1000-per-line/`'s own README: not a permanent verdict on `joingonka` (Gonka-network reliability moves on a timescale of minutes), not comparable to the 2026-09-18 TTFT figures given the different, heavier prompt mix used here, and n=200/line is a quick check, not a statistically-weighted replacement for the 1,000-request baseline.
