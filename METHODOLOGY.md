# Methodology

## What counts as a failure

A request counts as a failure if any of these hold:

- A non-2xx HTTP status.
- A connection-level error (timeout, connection refused, TLS failure)
  before any response arrived.
- A streaming response that started (some content arrived) but stalled
  or aborted before completion.

Every campaign used a fixed **15-second SLA per leg**: a request that
had not completed within 15 seconds was recorded as `timeout`, whether
or not it eventually would have completed on a longer wait. This bound
is arbitrary in the sense that a different number would produce
different absolute failure rates, but it is applied **identically** to
the direct leg and the gateway leg of every pair, so the *comparison*
between them (gateway vs. direct, same SLA) is unaffected by where
exactly the cutoff sits. See `phase3/results_phase3.jsonl`'s
`error_class`/`error_detail` fields for the raw classification of every
individual failure.

A non-2xx response with actual generated content in the body (rare, but
possible for some provider error shapes) is still counted as a failure -
"a real user got usable output" is the bar, not "the HTTP layer
returned a status we consider survivable."

## Pairing and McNemar's test

Phase 3 sends two requests per "pair": the same prompt, at (as close to)
the same instant as the benchmark harness can manage, one straight to
`proxygonka-deepseek` (bypassing the gateway entirely), one through the
gateway on the same line (Standard or Super Deal, alternating). Pairing
on the same prompt at the same instant controls for two obvious
confounds - prompt difficulty and provider-side conditions changing over
the course of a multi-day run - that an unpaired "N requests to A, then N
requests to B on a different day" design would not.

Because the two legs of a pair are not independent observations (they
share a prompt and a moment in time), the right significance test is
**McNemar's exact test**, not a two-proportion z-test. McNemar's ignores
the "both succeeded" and "both failed" pairs entirely (they carry no
information about which path is better) and asks, of the pairs where the
two paths *disagreed* (n = b + c, "discordant pairs"), whether the split
between "direct failed, gateway succeeded" (b) and "gateway failed,
direct succeeded" (c) looks like a fair coin flip. The exact test is a
two-sided binomial test on `min(b, c)` successes out of `n = b + c`
trials at p = 0.5 - the same definition `scipy.stats.binomtest` and R's
`binom.test` use. `scripts/mcnemar.py` implements this directly against
the raw JSONL with no external dependencies, so you can check our
arithmetic without installing anything.

**Why this matters, concretely**: an earlier, much smaller pilot (100
pairs, not included in this repo) had only 4 discordant pairs and a
McNemar p-value of 0.625 - genuinely uninformative, indistinguishable
from noise, and we said so at the time rather than publishing a
misleading headline number from too small a sample. Phase 3's 1,440
pairs produce 225 discordant pairs combined (150 for Standard alone),
enough for the McNemar test to return p < 1e-11 - a result we are
confident is real, not a sampling artifact.

## The provider-level benchmark

`provider_benchmark/` is a different, smaller, and simpler design: 25
direct (non-gateway) requests to *each* of the four providers
individually, unpaired, same 9-prompt bank as Phase 3 (3 categories:
short Q&A, long-context summarization, code generation), same 15s SLA
and failure classification. This measures each provider's own standalone
reliability during that window, not a gateway-vs-direct comparison - it
exists to answer "which specific provider is having a bad day," which
Phase 3's line-level aggregates can't distinguish (Standard and Super
Deal each mix multiple providers across their failover tiers).

## A snapshot, not a constant

Gonka-network provider reliability moves on a timescale of **minutes**,
not hours or days. During the provider benchmark, `proxygonka-deepseek`
measured 68% failure in one 25-request window; a separate check of 16
real gateway calls approximately 10-15 minutes later, in the same
session, found it succeeding on every single request with zero
failovers. Don't read any single provider's number in this repo as a
permanent verdict - it is an honest measurement of one specific window,
timestamped, and the network's condition can be materially different an
hour later in either direction.

## What this data does NOT claim

- It does not compare response *quality* between providers or between
  direct and gateway paths - only availability/completion within the SLA.
- It is not a claim that any specific provider is unreliable as a
  general, permanent fact - see the snapshot note above.
- The absolute failure-rate numbers (36.2%, 27.3%, etc.) are specific to
  this SLA, this prompt mix, and this time window - they are not a
  universal "Gonka network uptime" figure.
