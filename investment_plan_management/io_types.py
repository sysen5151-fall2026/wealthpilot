"""Input/Output entities of F.6 Manage Investment Plan Delivery.

Each class carries one Input/Output entity from the Innoslate model and is
named after it. The boundary flows of F.6 are Investment Recommendations and
Weights (from F.5, defined with the other first-level flows in model_flows),
the controls Explanation Rules (from X.3) and Plan Save Request (from X.1), and
four outputs to X.1. The internal flows between the second-level functions are
IO.6.1 Reviewed Plan Snapshot, IO.6.2 Authorized Plan Save Payload and IO.6.3
Plan Persistence Result.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from model_flows import InvestmentRecommendationsAndWeights, PlanMetrics, Recommendation  # noqa: F401 (re-exported)

# The only Plan Save Request action that authorizes a save (CS6.1.1.3).
EXPLICIT_SAVE = "save"

# Plan Persistence Result statuses reported by F.6.4.
SUCCEEDED = "succeeded"
REJECTED = "rejected"
FAILED = "failed"


@dataclass(frozen=True)
class ExplanationRules:
    """Explanation Rules: control from X.3 System Administrator to F.6.1 and F.6.2."""

    version: str
    scope_notice: str  # educational-simulation identifier shown with every plan
    risk_language: dict[str, str]  # identified-risk key -> novice-language sentence
    prohibited_phrases: list[str]
    learner_actions: list[str]  # the only controls offered to the learner

    def first_prohibited_phrase(self, text: str) -> str | None:
        """Return the first prohibited phrase that appears in text, or None."""
        lowered = text.lower()
        return next((p for p in self.prohibited_phrases if p.lower() in lowered), None)


@dataclass(frozen=True)
class InvestmentPlanExplanation:
    """Investment Plan Explanation: F.6.1 output to F.6.2 and X.1.

    The text fields follow the required output schema of the Model Response
    Contract in SPEC.md. plan_id and rules_version record which plan and which
    Explanation Rules the explanation belongs to.
    """

    plan_id: str
    rules_version: str
    summary: str
    allocation_rationale: list[str]
    material_risks: list[str]
    data_limitations: list[str]
    scope_notice: str
    historical_evidence: list[str] = field(default_factory=list)  # what the sample shows; never a forecast
    generated_by: str = "template"  # "template", or "language model <name>" (SPEC Model Response Contract)
    generation_note: str = ""  # why the template was used instead of the language model, if it was


@dataclass(frozen=True)
class ReviewedPlanSnapshot:
    """IO.6.1 Reviewed Plan Snapshot: the plan exactly as F.6.2 presented it."""

    plan_id: str
    scope_notice: str
    risk_category: str
    target_allocation: dict[str, float]
    recommendations: list[Recommendation]
    explanation: InvestmentPlanExplanation
    risk_score: int | None = None
    profile_basis: dict = field(default_factory=dict)  # the planning inputs the plan reflects (SR-01)
    simulated_amounts: dict = field(default_factory=dict)  # what each weight means in USD; nothing moves
    plan_metrics: PlanMetrics | None = None
    data_snapshot_id: str | None = None
    rules_configuration_id: str | None = None


@dataclass(frozen=True)
class PresentedInvestmentPlan:
    """Presented Investment Plan: F.6.2 output to X.1 Individual Investor."""

    plan_id: str
    display_text: str
    learner_actions: list[str]
    content: dict = field(default_factory=dict)  # the Reviewed Plan Snapshot as data, for the browser


@dataclass(frozen=True)
class PlanSaveRequest:
    """Plan Save Request: control from X.1 Individual Investor to F.6.3, F.6.4 and F.6.5."""

    request_id: str
    plan_id: str
    action: str  # EXPLICIT_SAVE, or an implicit event such as "view", "open" or "close"


@dataclass(frozen=True)
class AuthorizedPlanSavePayload:
    """IO.6.2 Authorized Plan Save Payload: F.6.3 output to F.6.4."""

    reviewed_plan: ReviewedPlanSnapshot
    authorization: PlanSaveRequest


@dataclass(frozen=True)
class PlanPersistenceResult:
    """IO.6.3 Plan Persistence Result: F.6.4 output to F.6.5."""

    status: str  # SUCCEEDED, REJECTED or FAILED
    plan_id: str
    request_id: str
    persisted_plan: dict | None  # the record as read back; None unless SUCCEEDED
    detail: str


@dataclass(frozen=True)
class SavedInvestmentPlan:
    """Saved Investment Plan: F.6.5 output to X.1."""

    plan_id: str
    content: dict  # the persisted record referenced by the Plan Persistence Result


@dataclass(frozen=True)
class SavedPlanConfirmation:
    """Saved Plan Confirmation: F.6.5 output to X.1."""

    plan_id: str
    request_id: str
    message: str
