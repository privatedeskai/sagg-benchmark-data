# Real request traces

Raw output of SAGG's own per-request tracing tool
(`GET /internal/admin/request-trace?request_id=<id>`) - the exact
chronology of every tier a single request attempted, with millisecond
timestamps and an explicit `pre_generation` vs `mid_generation` failure
classification (did the failure happen before any content was generated,
or partway through an already-started stream).

Provenance of each file, stated plainly rather than left ambiguous:

- **`trace_full_cascade_097c128a313f865f.json`** - **fully real, unforced
  production traffic.** A genuine customer-facing request on the
  Standard line: Tier1 (`proxygonka-deepseek`) timed out at 3.0s, Tier2
  (`eterial-deepseek`) ALSO timed out at its own 12s budget, Tier3
  (`deepinfra-deepseek`) succeeded in 436ms. Total end-to-end latency
  15.4s - slow, but the request succeeded instead of failing outright.
  This is the single most illustrative trace in this repo: it shows the
  exact failure mode the provider benchmark's headline finding describes
  (multiple Gonka-network brokers degraded at once) actually happening to
  a real request, and the gateway's fallback surviving it.

- **`trace_tier1_to_tier2_68d107e79328b552.json`** - real production
  traffic. Tier1 timed out at 3.0s, Tier2 (`eterial-deepseek`) succeeded.

- **`trace_healthy_path_4884c2bb7baa1870.json`** - real production
  traffic, the common case: Tier1 succeeded directly, 33ms total.

- **`trace_full_failure_aedb0462d446ed4c.json`** - **not real traffic.**
  Captured from an isolated test instance with all three tiers pointed at
  deliberately unreachable addresses, to show what the trace format looks
  like when every tier genuinely fails (`all_providers_exhausted`).
  Included for completeness of the format, not as evidence of a real
  outage - no real production request has ever failed all three tiers
  during the periods measured in this repo.
