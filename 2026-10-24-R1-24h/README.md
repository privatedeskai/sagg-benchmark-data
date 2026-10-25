# R1, 24-hour test: data and scripts

Version R1, 2026-10-23 20:00 to 2026-10-24 19:59 (UTC-7). Providers anonymised; no keys; unique synthetic prompts.

* `main_requests.csv` - one row per request of the main load (both lines): class, stream, status, served, valid, first-text and total time, tokens, finish reason, request id.
* `pairs_standard.csv`, `pairs_superdeal.csv` - gateway against direct, one row per pair.
* `agent_*.csv` - the four-tool-call scenario, one row per run.
* `golden_v1/` - strict extraction set, gateway and direct (one file per pass).
* `canada_r1b.csv` - the separate client-place measurement (night hours, indicative).
* `compatibility_matrix.jsonl`, `hourly_*.csv`, `per_class.md`, `request_provider.csv` (serving provider as Provider A/B/C or insurance provider), `summary.json` (every figure).
* `analyze.py` - recomputes the headline figures (standard library only): `python3 analyze.py main_requests.csv`.

Definitions: served = HTTP 200 with a complete answer; first text = time to the first content token of served streaming requests; Wilson 95 % intervals, bootstrap 95 % for percentiles, exact McNemar for pairs. The 99th percentile is an estimate from one daily cycle. Accuracy at 200,000 tokens was not part of this test (measured earlier on version be46d49).
(the last digit of a percentile can differ by one between summary.json and analyze.py: summary.json stores values rounded to one decimal)
