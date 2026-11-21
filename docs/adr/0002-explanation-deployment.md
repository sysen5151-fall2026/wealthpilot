# ADR-0002 Explain investment plans

**Status** Accepted for the course pilot. Use on-host explanation processing with the deterministic template enabled by default. Optional model inference is limited to a loopback endpoint on the same host.

## Context

[Innoslate decision](https://cloud.innoslate.com/cornell/p/813/database/entity/319193) compares local model inference with a hosted API for F.6.1. The current code has an opt-in LM Studio adapter and a template. ADR-0001 proposes local hosting. It calls for revisiting the choice against the pilot timing criterion.

## Evaluation

Score comprehension (SA-01), factual fidelity (SA-02), p95 explanation-to-display latency (SA-03), off-host data exposure (SA-04), and lifecycle cost with an affordability check (SA-05). Treat the template as a third reference path.

The course simulation assumes 1,000 explanations and a $250 ceiling. The team confirmed swing points of 80, 100, 40, 50, and 30 for SA-01 through SA-05, respectively.

| Option | Comprehension | Fidelity | Display p95 | Off-host fields | Lifecycle cost | Weighted score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Local model | 82% | 96% | 8.0 s | 0% | $160 | 74.1% |
| Hosted API | 90% | 96% | 1.4 s | 40% | $100 | 76.0% |
| Deterministic template | 80% | 100% | 0.25 s | 0% | $60 | 90.6% |

All table inputs are scenario assumptions. Normalize the swing points by their sum. Comprehension and fidelity values equal their rates. Latency and cost use declining linear values, floored at zero, with anchors of 2.0 s and $250. Data exposure value equals one minus the off-host field share. Reducing the latency swing to 15 gives local inference 80.9% and the hosted API 80.2%. The template ranks first with latency swings of 15, 40, and 80.

Separately, the [local inference spike](../evidence/explanation-deployment-spike.md) returned six model explanations in 8.64 to 18.68 s on CPU before browser display. The in-process template baseline was 0.0959 ms p95 over 100 repeats of one synthetic fixture. The hosted candidate would need an approved payload boundary and provider configuration. A deployment beyond the course simulation would still need user comprehension, end-to-end timing and cost validation.

## Implementation implications

- A local model requires an installed runtime, pinned compatible model, resource and license checks, and evidence that it satisfies the pilot timing requirement before being enabled.
- A hosted API would require a provider-specific authenticated adapter, approved data handling, a minimized payload, failure handling and a budget tied to pilot request volume.
- Both candidates require validation and deterministic fallback at F.6.1 so an invalid explanation does not reach F.6.2.

The implementation enforces loopback at the point of inference, disables HTTP redirection and uses the template when model configuration or the response fails. Revisit the pilot configuration when a faster local model has been verified or an off-host payload and provider have been approved.
