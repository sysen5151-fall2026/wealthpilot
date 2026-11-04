"""F.6.5 Confirm Successful Plan Save, performed by C.6.5 Save Confirmation Component.

Satisfies CS6.1.4.5; also CS6.1.2.3, CS6.1.2.4 and the C.6.5 part of CS6.1.1.3.

ICOM from the second-level IDEF0 of F.6:
    input      IO.6.3 Plan Persistence Result (from F.6.4, over IF.6.4)
    control    Plan Save Request (from X.1, over EF.21)
    outputs    Saved Investment Plan (to X.1, over EF.21)
               Saved Plan Confirmation (to X.1, over EF.21)
    mechanism  C.6.5 Save Confirmation Component
"""

from .io_types import (
    SUCCEEDED,
    PlanPersistenceResult,
    PlanSaveRequest,
    SavedInvestmentPlan,
    SavedPlanConfirmation,
)


def confirm_successful_plan_save(
    plan_persistence_result: PlanPersistenceResult,
    *,
    plan_save_request: PlanSaveRequest,
) -> tuple[SavedInvestmentPlan, SavedPlanConfirmation] | None:
    """Release the saved plan and its confirmation only after a successful save.

    Returns None for a rejected, failed, pending or indeterminate result, and
    for a result that does not belong to this request and its plan.
    """
    result = plan_persistence_result
    if result.status != SUCCEEDED or result.persisted_plan is None:
        return None
    if (result.request_id, result.plan_id) != (plan_save_request.request_id, plan_save_request.plan_id):
        return None
    if result.persisted_plan.get("plan_id") != result.plan_id:
        return None

    saved_plan = SavedInvestmentPlan(plan_id=result.plan_id, content=result.persisted_plan)
    confirmation = SavedPlanConfirmation(
        plan_id=result.plan_id,
        request_id=result.request_id,
        message=f"Simulated plan {result.plan_id} is saved. No real trade was placed and no money moved.",
    )
    return saved_plan, confirmation
