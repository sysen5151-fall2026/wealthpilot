"""F.6.3 Validate Explicit Plan Save Request, performed by C.6.3 Save Authorization Component.

Satisfies CS6.1.4.3; also the C.6.3 part of CS6.1.1.3.

ICOM from the second-level IDEF0 of F.6:
    input      IO.6.1 Reviewed Plan Snapshot (from F.6.2, over IF.6.2)
    control    Plan Save Request (from X.1, over EF.20)
    output     IO.6.2 Authorized Plan Save Payload (to F.6.4, over IF.6.3)
    mechanism  C.6.3 Save Authorization Component
"""

from .io_types import (
    EXPLICIT_SAVE,
    AuthorizedPlanSavePayload,
    PlanSaveRequest,
    ReviewedPlanSnapshot,
)


def validate_explicit_plan_save_request(
    reviewed_plan_snapshot: ReviewedPlanSnapshot,
    *,
    plan_save_request: PlanSaveRequest | None,
) -> AuthorizedPlanSavePayload | None:
    """Authorize the save only for an explicit request that matches the reviewed plan.

    Returns None, so no payload exists, for an absent, implicit, invalid or
    mismatched request.
    """
    if plan_save_request_problem(reviewed_plan_snapshot, plan_save_request) is not None:
        return None
    return AuthorizedPlanSavePayload(
        reviewed_plan=reviewed_plan_snapshot,
        authorization=plan_save_request,
    )


def plan_save_request_problem(
    reviewed_plan_snapshot: ReviewedPlanSnapshot,
    plan_save_request: PlanSaveRequest | None,
) -> str | None:
    """Say why a request cannot authorize a save, or return None if it can."""
    if plan_save_request is None:
        return "no Plan Save Request was received"
    if plan_save_request.action != EXPLICIT_SAVE:
        return f"'{plan_save_request.action}' is not an explicit save request"
    if not plan_save_request.request_id:
        return "the Plan Save Request has no request ID"
    if plan_save_request.plan_id != reviewed_plan_snapshot.plan_id:
        return "the Plan Save Request refers to a different or superseded plan"
    return None
