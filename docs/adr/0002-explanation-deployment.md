# ADR-0002 Explain investment plans

**Status** Proposed. Keep the deterministic template enabled by default for the pilot build while the deployment comparison is open.

## Context

[Innoslate decision](https://cloud.innoslate.com/cornell/p/813/database/entity/319193) compares local model inference with a hosted API for F.6.1. The current code has an opt-in LM Studio adapter and a template. ADR-0001 proposes local hosting. It calls for revisiting the choice against the pilot timing criterion.

## Evaluation

Score comprehension (SA-01), factual fidelity (SA-02), p95 explanation-to-display latency (SA-03), off-host data exposure (SA-04), and lifecycle cost with an affordability check (SA-05). Use the same synthetic plans, scoring rules, explanation contract and workload for both candidates. Treat the template as a third reference path. The current in-process template baseline was 0.0959 ms p95 in 100 repeats of one synthetic fixture. Browser display and model inference are outside that observation. The local and hosted candidates lack paired measurements and the team has yet to approve a hosted payload boundary and pilot budget.

## Implementation implications

- A local model requires an installed runtime, pinned compatible model, resource and license checks, and verification that the configured endpoint stays on the host.
- A hosted API requires a provider-specific authenticated adapter, approved data handling, a minimized payload, failure handling and a budget tied to pilot request volume.
- Both candidates require validation and deterministic fallback at F.6.1 so an invalid explanation does not reach F.6.2.

Record the winning candidate, verified scores and implementation commit after pilot measurements. Until those inputs are available, the existing template is the operational default.
