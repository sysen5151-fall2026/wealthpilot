"""Investor-facing side of UC.1 (walking-skeleton stubs).

The request functions belong to F.1 Collect Investor Information, performed by
C.1 Investor Information Interface; the values they return stand in for the
answers of X.1 Individual Investor and are hard-coded at this increment. The
other functions show WealthPilot outputs to the investor or return the
investor's decisions.
"""

from investment_plan_management import (
    EXPLICIT_SAVE,
    PlanSaveRequest,
    PresentedInvestmentPlan,
    SavedInvestmentPlan,
    SavedPlanConfirmation,
)


def initiate_session() -> str:
    return "session-001"


def request_financial_profile(session_id: str) -> dict:
    return {
        "age": 30,
        "income": 80000,
        "savings": 20000,
        "goal": "retirement",
        "horizon_years": 20,
        "liquidity_needs": "low",
    }


def provide_risk_questionnaire_response() -> dict:
    return {
        "risk_tolerance": 3,
        "risk_capacity": 4,
        "experience": "beginner",
        "max_loss": 0.2,
    }


def provide_current_holdings() -> list:
    return [
        {"ticker": "VTI", "value": 5000}
    ]


def present_risk_assessment(risk_score_and_category: dict) -> None:
    """UC.1.9: show the Risk Score and Risk Category to the investor."""
    print("SIMULATED EDUCATIONAL OUTPUT")
    print(
        f"Risk score: {risk_score_and_category['risk_score']} "
        f"({risk_score_and_category['risk_category']})"
    )


def confirm_profile_interpretation() -> bool:
    """UC.1.10: the investor confirms the profile interpretation (always yes here)."""
    return True


def view_presented_plan(presented_plan: PresentedInvestmentPlan) -> None:
    """UC.1.17: the investor sees the Presented Investment Plan."""
    print(presented_plan.display_text)


def request_plan_save(
    presented_plan: PresentedInvestmentPlan, *, wants_to_save: bool
) -> PlanSaveRequest | None:
    """UC.1.18: an explicit save request for the plan on screen, or none at all."""
    if not wants_to_save:
        return None
    return PlanSaveRequest(
        request_id="save-request-001",
        plan_id=presented_plan.plan_id,
        action=EXPLICIT_SAVE,
    )


def review_saved_plan(
    saved_plan: SavedInvestmentPlan, confirmation: SavedPlanConfirmation
) -> None:
    """UC.1.20: the investor reviews the Saved Investment Plan and its confirmation."""
    print(confirmation.message)
    holdings = ", ".join(
        f"{r['symbol']} {r['weight']:.0%}" for r in saved_plan.content["recommendations"]
    )
    print(f"Saved plan on record: {holdings}")
