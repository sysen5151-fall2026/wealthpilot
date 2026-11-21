# ADR-0002 Explain investment plans

**Status** Accepted for the course pilot. Use on-host explanation processing with the deterministic template enabled by default. Optional model inference is limited to a loopback endpoint on the same host.

## Context

[Innoslate decision](https://cloud.innoslate.com/cornell/p/813/database/entity/319193) compares local model inference with a hosted API for F.6.1. The scaffold included the template as a working default and failure fallback while ADR-0001 proposed a local model and left deployment open for the Week 12 timing comparison. ADR-0002 selects the template as the course pilot architecture.

## Evaluation

Score comprehension (SA-01), factual fidelity (SA-02), p95 explanation-to-display latency (SA-03), off-host data exposure (SA-04), and lifecycle cost with an affordability check (SA-05). Treat the template as a third reference path.

The course simulation models 1,000 explanations and an analysis ceiling of $250, derived from 10 assumed hours at $25/h. Fidelity has critical importance and a small 0.04 scenario value spread. Comprehension has high importance and a small 0.10 spread. Exposure has high importance and a large 1.00 spread. Latency has moderate importance and a large 0.875 spread. Cost has lower importance and a medium 0.40 spread. The updated course study uses 80, 100, 40, 80 and 30 swing points for SA-01 through SA-05 (330 total). SA-04 ties SA-01 because both are rated High and SA-04 covers the larger spread.

| Option | Comprehension | Fidelity | Latency input | Off-host categories | Lifecycle cost | Weighted score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Local model | 82% | 96% | 17.35 s component p95 | 0 of 5 | $160.00 | 76.48% |
| Hosted GPT-4.1 mini | 90% | 96% | 3.69 s benchmark proxy | 5 of 5 | $85.69 | 56.88% |
| Deterministic template | 80% | 100% | 0.25 s assumed | 0 of 5 | $60.00 | 91.45% |

Comprehension and fidelity inputs are scenario assumptions. Fidelity (SA-02) uses all replies as its denominator. Comprehension (SA-01) uses only fidelity-pass replies in each N-02 task and takes the lower pass rate of the two tasks. A factual failure contributes only to SA-02. Latency and cost use declining linear values floored at zero, with anchors of 2.0 s and $250. Exposure value equals one minus the off-host category share. The hosted comparison forwards the existing explanation contract and covers all five designated categories if deployed. The current pilot sends no explanation payload off host.

The engineering estimates use 4.0/1.6 setup/support hours for local inference, 2.2/1.2 for hosted and 1.6/0.6 for the template. Modeled on-host overhead is $20 and $5, respectively. Hosted usage allows 1,000 input tokens per request and uses 180 output tokens. Codex counted 180 tokens with tiktoken 0.14.0 (o200k_base) after serializing the five response fields in the synthetic template fixture as compact JSON. This workload sample excludes provider framing overhead. [Published standard text rates](https://developers.openai.com/api/docs/models/gpt-4.1-mini) of $0.40 and $1.60 per million tokens give $0.688 for the modeled workload. [BenchLeader’s OpenAI provider row](https://www.benchleader.com/models/gpt-4-1-mini) showed a 1.02 s first token and 67 tokens/s in the snapshot accessed 2026-11-21. The proxy, 1.02 + (180 − 1)/67 = 3.69 s, exceeds the 2.0 s anchor and gives zero latency value. This proxy excludes WealthPilot rendering and is not a pilot p95. GPT-4.1 mini remains a historical study comparator.

With the non-comprehension weights rescaled proportionally, hosted ties template at 83.00% comprehension weight. At the baseline weight of 24.24%, hosted scores at most 59.31% with perfect comprehension. The template scores 72.06% even at zero comprehension. That margin is specific to the assumed costs and other inputs. A hosted test would need an approved payload and configured provider.

The [local inference spike](../evidence/explanation-deployment-spike.md) used six CPU runs before browser display (8.64–18.68 s). The linearly interpolated sample p95 is 17.35 s, and each measured run exceeded the 2.0 s display anchor before rendering. The in-process template baseline was 0.0959 ms p95 over 100 repeats. Learner comprehension and hosted end-to-end latency remain unmeasured.

## Implementation implications

- A local model requires an installed runtime, pinned compatible model, resource and license checks, and evidence that it satisfies the pilot timing requirement before being enabled.
- A hosted API would require a provider-specific authenticated adapter, approved data handling, a minimized payload, failure handling and a budget tied to pilot request volume.
- Both candidates require validation and deterministic fallback at F.6.1 so an invalid explanation does not reach F.6.2.

The implementation enforces loopback at the point of inference, disables HTTP redirection and uses the template when model configuration or the response fails. Revisit the pilot configuration when a faster local model has been verified or an off-host payload and provider have been approved.
