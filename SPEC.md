# SPEC.md

## Needs and Acceptance Criteria

### N-01 — Coherent Planning
**Need statement:** I need the planning result to consistently reflect my stated goal, horizon, financial capacity, and hypothetical holdings.

**Traces to:**
- **SR-01 — Planning Result Consistency:** WealthPilot shall generate and present the planning result using the investor’s stated goal, investment horizon, financial capacity, and hypothetical holdings as planning inputs.

**Acceptance criterion:** At least **9 of 10** synthetic profiles show that all four stated planning inputs are represented consistently in the resulting plan during an independent review.

---

### N-02 — Comprehension
**Need statement:** I need the plan rationale and material risks to be understandable to a novice learner.

**Traces to:**
- **SR-02 — Profile-to-Allocation Explanation:** WealthPilot shall explain how the investor profile and risk assessment are used to determine the proposed allocation.
- **SR-03 — Plan Risk Explanation:** WealthPilot shall explain at least one identified investment risk associated with the proposed plan using language defined for the novice-investor pilot.

**Acceptance criterion:** At least **8 of 10** novice learners correctly explain two profile or risk factors that influenced the allocation without facilitator prompting, and at least **8 of 10** identify and explain one plan risk in their own words after UC.1.

---

### N-03 — User Control
**Need statement:** I need saving a plan and approving a later simulated portfolio change to remain distinct decisions under my control.

**Traces to:**
- **SR-04 — Explicit Plan Save Confirmation:** WealthPilot shall require explicit investor confirmation before storing a proposed plan as the saved plan.
- **SR-05 — Plan Save State Preservation:** WealthPilot shall preserve simulated cash and holdings when the investor saves a planning result.
- **SR-06 — Separate Simulated Change Approval:** WealthPilot shall require separate explicit investor approval before applying a simulated portfolio change.

**Acceptance criterion:** In **10 of 10** observed pilot trials, learners identify the plan-save confirmation step, no plan is stored before confirmation, saving does not change simulated cash or holdings, and learners distinguish plan saving from later simulated-change approval.

---

### N-04 — Goal-Based Exploration
**Need statement:** I need to compare changed planning assumptions with an unchanged baseline and understand the effect on my hypothetical goal.

**Traces to:**
- **SR-07 — What-If Scenario Preservation:** WealthPilot shall create a what-if scenario from at least one changed planning assumption while preserving the saved baseline unchanged.
- **SR-08 — Scenario Effect Presentation:** WealthPilot shall present the change in progress toward the stated hypothetical goal between the saved baseline and the what-if scenario using the same comparison method.

**Acceptance criterion:** At least **8 of 10** learners create a what-if scenario, correctly identify that the saved baseline is unchanged, and correctly explain the direction of the scenario’s effect on the hypothetical goal.

---

### N-05 — Suitable Historical Data
**Need statement:** I need the historical evidence used in the exercise to be fit for the selected analysis and its limitations to be visible.

**Traces to:**
- **SR-09 — Historical Data Admission:** WealthPilot shall admit historical data to planning or replay only when the data satisfy the approved historical-data contract.
- **SR-10 — Historical Data Limitation Disclosure:** WealthPilot shall present the applicable historical-data limitation when required data fail the approved historical-data contract.

**Acceptance criterion:** **100%** of instruments admitted to the pilot satisfy every required historical-data-contract check for the selected replay interval, and **100%** of seeded missing-data cases display the applicable limitation before the affected result can be interpreted as valid.

---

### N-06 — Reproducible Operation
**Need statement:** I need an approved educational exercise to be reproducible and recoverable from a documented baseline.

**Traces to:**
- **SR-11 — Exercise Reproduction:** WealthPilot shall enable an authorized System Administrator to reproduce an approved educational exercise using the approved educational baseline.
- **SR-12 — Baseline Recovery:** WealthPilot shall enable an authorized System Administrator to restore the approved educational baseline after a controlled recovery exercise.

**Acceptance criterion:** Two independent operators reproduce the same saved-plan version and simulated-ledger balances from the approved educational baseline, and two controlled recovery exercises restore matching configuration identifiers, saved-plan version, and simulated-ledger balances.

---

### N-07 — Honest Educational Scope
**Need statement:** I need WealthPilot’s educational and simulated scope to remain clear at the points where learners make decisions.

**Traces to:**
- **SR-13 — Educational Simulation Identification:** WealthPilot shall display an educational-simulation identifier at every modeled learner decision point involving a planning output or simulated portfolio action.
- **SR-14 — Learner Interface Scope:** WealthPilot shall expose only educational planning and internal-simulation controls through the learner interface.

**Acceptance criterion:** **10 of 10** pilot learners correctly identify WealthPilot as an educational simulator and distinguish simulated actions from real investment execution, and **100%** of learner-interface screens pass the boundary review with no brokerage-credential, real-order, or real-fund-transfer control.

---

### N-08 — Usable Educational Exercise
**Need statement:** I need novice learners to complete the primary planning exercise with limited facilitator assistance and demonstrate basic understanding.

**Traces to:**
- **SR-15 — Independent UC.1 Completion:** WealthPilot shall support completion of UC.1 by a novice learner following the approved pilot instructions without facilitator intervention during the modeled UC.1 workflow.

**Acceptance criterion:** At least **8 of 10** novice learners complete UC.1 without facilitator intervention; all assistance events and task barriers are recorded.

---

## Data Contract

### Purpose
This contract governs historical market data admitted to WealthPilot planning and replay exercises. It supports N-05, SR-09, and SR-10.

### Boundary and source
- Data are provided by **X.2 Market Data Provider**.
- WealthPilot uses **historical** data for the educational simulator; real-time execution quotes are out of scope.
- The current scaffold uses hard-coded sample prices. A later implementation that connects an external provider must document the actual provider and endpoint in `docs/adr/environment.md`.

### Required logical fields

| Field | Type | Format / unit | Admission rule |
|---|---|---|---|
| `symbol` | string | security identifier / ticker | Required and non-empty |
| `date` | date | ISO 8601 `YYYY-MM-DD` | Required; unique per symbol/date |
| `adjusted_close` | number | quote currency per share | Required; finite and > 0 |

Provider-native fields such as `open`, `high`, `low`, `close`, `volume`, split factors, or dividend fields may be retained. When adjusted historical prices are required by the selected exercise, WealthPilot calculations use the documented adjusted-price field.

### Coverage and ordering
- Records must be sortable by `date`.
- Duplicate `symbol + date` records are rejected until resolved.
- The selected replay interval must contain enough valid observations for the configured analysis. The minimum observation count is an exercise configuration item and must be documented when implementation begins.

### Invalid or incomplete data
A dataset fails admission when a required logical field is missing, null, malformed, non-finite, or when `adjusted_close <= 0`.

Missing observations or insufficient interval coverage are surfaced as a **historical-data limitation**. WealthPilot withholds the affected analysis rather than silently treating incomplete evidence as complete.

### Replay and reproducibility
- Historical datasets used in an approved educational baseline are versioned or fingerprinted.
- A replay uses the approved dataset version for that exercise rather than silently substituting newer data.

### Provider unavailable
If the Market Data Provider is unavailable, WealthPilot does not fabricate historical observations. The learner is shown the applicable data-source limitation and the affected analysis is withheld.

---

## Model Response Contract

### Purpose
This contract governs the language-model explanation layer. The language model explains an authoritative WealthPilot planning result; it does not select or execute real investments.

### Authority boundary
- Risk Score, risk level, target allocation, candidate-security list, weights, and quantitative risk metrics are authoritative outputs of the deterministic WealthPilot rules / analysis layer.
- The explanation layer may explain those outputs but must not silently alter them.
- Brokerage credentials, real orders, real fund transfers, and live-account execution are out of scope.

### Current scaffold status
The current `ai_explanation_model.compose_explanation()` function returns a fixed demonstration string. It does **not yet satisfy** the structured response contract below. This is expected at the Task 2 increment and is captured by the red acceptance-test suite.

### Input schema

```json
{
  "risk_score": 0,
  "risk_level": "Conservative | Moderately Conservative | Moderate | Moderately Aggressive | Aggressive",
  "planning_inputs": {
    "goal": "string",
    "investment_horizon": "string",
    "financial_capacity": "string",
    "liquidity_needs": "string",
    "experience": "string"
  },
  "target_allocation": [
    {"asset_class": "string", "weight": 0.0}
  ],
  "candidate_securities": [
    {"symbol": "string", "weight": 0.0, "risk_metrics": {}}
  ],
  "identified_risks": ["string"],
  "data_limitations": ["string"]
}
```

### Required output schema

```json
{
  "summary": "plain-language explanation",
  "allocation_rationale": ["string"],
  "material_risks": ["string"],
  "data_limitations": ["string"],
  "scope_notice": "Educational simulation only; no real trade is executed."
}
```

### Response constraints
- `summary` is non-empty.
- `allocation_rationale` references only supplied investor/planning information and authoritative plan outputs.
- `material_risks` contains at least one item when the upstream plan supplies one or more identified risks.
- `data_limitations` preserves upstream limitations and does not suppress them.
- `scope_notice` clearly identifies the output as educational and simulated.
- The response must not claim that a real order was placed, funds were transferred, or a brokerage account was accessed.

### Malformed or contradictory response
If a response is missing a required field, cannot be parsed to the expected schema, or contradicts the authoritative planning output, WealthPilot rejects it and uses a deterministic explanation template generated from the approved planning result.

### Local model assumption
The project environment identifies **LM Studio** as the intended local runner. The exact open-source model has not yet been selected or integrated in this scaffold. When it is selected, update `docs/adr/environment.md` without changing this contract unless the approved system model changes.
