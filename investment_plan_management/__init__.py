"""C.6 Investment Plan Management Subsystem: performs F.6 Manage Investment Plan Delivery.

F.6 is decomposed on its second-level IDEF0 into five functions, one module each:

    F.6.1 Explain Investment Plan               explanation_engine.py   C.6.1 Explanation Engine
    F.6.2 Present Investment Plan               plan_presentation.py    C.6.2 Plan Presentation Component
    F.6.3 Validate Explicit Plan Save Request   save_authorization.py   C.6.3 Save Authorization Component
    F.6.4 Persist Reviewed Investment Plan      plan_repository.py      C.6.4 Plan Repository Component
    F.6.5 Confirm Successful Plan Save          save_confirmation.py    C.6.5 Save Confirmation Component

The flows between them are defined in io_types.py. Requirements come from the
CS.6 component specification in the Innoslate model.
"""

from .explanation_engine import explain_investment_plan
from .io_types import (
    EXPLICIT_SAVE,
    FAILED,
    REJECTED,
    SUCCEEDED,
    AuthorizedPlanSavePayload,
    ExplanationRules,
    InvestmentPlanExplanation,
    InvestmentRecommendationsAndWeights,
    PlanPersistenceResult,
    PlanSaveRequest,
    PresentedInvestmentPlan,
    Recommendation,
    ReviewedPlanSnapshot,
    SavedInvestmentPlan,
    SavedPlanConfirmation,
)
from .plan_presentation import present_investment_plan
from .plan_repository import JsonPlanStore, PlanStore, persist_reviewed_investment_plan
from .save_authorization import plan_save_request_problem, validate_explicit_plan_save_request
from .save_confirmation import confirm_successful_plan_save

__all__ = [
    "EXPLICIT_SAVE",
    "FAILED",
    "REJECTED",
    "SUCCEEDED",
    "AuthorizedPlanSavePayload",
    "ExplanationRules",
    "InvestmentPlanExplanation",
    "InvestmentRecommendationsAndWeights",
    "JsonPlanStore",
    "PlanPersistenceResult",
    "PlanSaveRequest",
    "PlanStore",
    "PresentedInvestmentPlan",
    "Recommendation",
    "ReviewedPlanSnapshot",
    "SavedInvestmentPlan",
    "SavedPlanConfirmation",
    "confirm_successful_plan_save",
    "explain_investment_plan",
    "persist_reviewed_investment_plan",
    "plan_save_request_problem",
    "present_investment_plan",
    "validate_explicit_plan_save_request",
]
