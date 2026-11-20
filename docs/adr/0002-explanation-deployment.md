# ADR-0002 Explain investment plans

**Status** Accepted for the course pilot. Use on-host explanation processing with the deterministic template enabled by default. Optional model inference is limited to a loopback endpoint on the same host.

## Context

[Innoslate decision](https://cloud.innoslate.com/cornell/p/813/database/entity/319193) compares local model inference with a hosted API for F.6.1. The current code has an opt-in LM Studio adapter and a template. ADR-0001 proposes local hosting. It calls for revisiting the choice against the pilot timing criterion.

## Evaluation

Score comprehension (SA-01), factual fidelity (SA-02), p95 explanation-to-display latency (SA-03), off-host data exposure (SA-04), and lifecycle cost with an affordability check (SA-05). Treat the template as a third reference path.

The in-process template baseline was 0.0959 ms p95 in 100 repeats of one synthetic fixture. The [local inference spike](../evidence/explanation-deployment-spike.md) returned six model explanations on CPU. All six took more than the provisional 2.0 s explanation-to-display budget before browser display. The hosted candidate has no approved payload boundary or provider configuration for the pilot. These feasibility findings support the local template pilot configuration. Paired measurements, comprehension results and full lifecycle cost remain open, so a complete numerical ranking is unavailable.

## Implementation implications

- A local model requires an installed runtime, pinned compatible model, resource and license checks, and evidence that it satisfies the pilot timing requirement before being enabled.
- A hosted API would require a provider-specific authenticated adapter, approved data handling, a minimized payload, failure handling and a budget tied to pilot request volume.
- Both candidates require validation and deterministic fallback at F.6.1 so an invalid explanation does not reach F.6.2.

The implementation enforces loopback at the point of inference, disables HTTP redirection and uses the template when model configuration or the response fails. Revisit the pilot configuration when a faster local model has been verified or an off-host payload and provider have been approved.
