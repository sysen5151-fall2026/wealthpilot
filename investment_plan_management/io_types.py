"""Input/Output entities of F.6 Manage Investment Plan Delivery.

Each class carries one Input/Output entity from the Innoslate model and is
named after it. The boundary flows of F.6 are Investment Recommendations and
Weights (from F.5), the controls Explanation Rules (from X.3) and Plan Save
Request (from X.1), and four outputs to X.1. The internal flows between the
second-level functions are IO.6.1 Reviewed Plan Snapshot, IO.6.2 Authorized
Plan Save Payload and IO.6.3 Plan Persistence Result.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

# The only Plan Save Request action that authorizes a save (CS6.1.1.3).
EXPLICIT_SAVE = "save"

# Plan Persistence Result statuses reported by F.6.4.
SUCCEEDED = "succeeded"
REJECTED = "rejected"
FAILED = "failed"


@dataclass(frozen=True)
class Recommendation:
    """One recommended security and its weight in the simulated portfolio."""

    symbol: str
    asset_class: str
    weight: float  # share of the simulated portfolio, 0 to 1


@dataclass(frozen=True)
class InvestmentRecommendationsAndWeights:
    """Investment Recommendations and Weights: F.5 output, F.6 input (IF.6).

    Carries the risk basis recorded upstream, so F.6.1 can explain how the
    risk assessment led to the allocation.
    """

    risk_score: int
    risk_category: str
    target_allocation: dict[str, float]  # asset class -> share of the portfolio
    recommendations: list[Recommendation]
    identified_risks: list[str]  # keys into ExplanationRules.risk_language
    data_limitations: list[str]

    @property
    def plan_id(self) -> str:
        """Identity of this plan, derived from its content.

        A plan with different content gets a different identity, so a save
        request for a superseded plan no longer matches (CS6.1.4.3).
        """
        content = json.dumps(asdict(self), sort_keys=True)
        return "plan-" + hashlib.sha256(content.encode()).hexdigest()[:10]


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


@dataclass(frozen=True)
class ReviewedPlanSnapshot:
    """IO.6.1 Reviewed Plan Snapshot: the plan exactly as F.6.2 presented it."""

    plan_id: str
    scope_notice: str
    risk_category: str
    target_allocation: dict[str, float]
    recommendations: list[Recommendation]
    explanation: InvestmentPlanExplanation


@dataclass(frozen=True)
class PresentedInvestmentPlan:
    """Presented Investment Plan: F.6.2 output to X.1 Individual Investor."""

    plan_id: str
    display_text: str
    learner_actions: list[str]


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
