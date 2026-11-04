"""C.0 WealthPilot: runs UC.1 through F.1 to F.5 and the five functions of F.6.

This module is the orchestration, not a function on the IDEF0. It calls each
function in UC.1 order and prints one trace line per step, tagged with the
function and the asset that performs it (for example [F.6.3 | C.6.3]), so a
run can be followed on the IDEF0 diagrams.
"""

from pathlib import Path
from typing import NamedTuple

from allocation_engine import determine_target_asset_allocation
from investment_plan_management import (
    InvestmentRecommendationsAndWeights,
    JsonPlanStore,
    PlanStore,
    PresentedInvestmentPlan,
    SavedInvestmentPlan,
    SavedPlanConfirmation,
    confirm_successful_plan_save,
    explain_investment_plan,
    persist_reviewed_investment_plan,
    plan_save_request_problem,
    present_investment_plan,
    validate_explicit_plan_save_request,
)
from investor_interface import (
    confirm_profile_interpretation,
    initiate_session,
    present_risk_assessment,
    provide_current_holdings,
    provide_risk_questionnaire_response,
    request_financial_profile,
    request_plan_save,
    review_saved_plan,
    view_presented_plan,
)
from market_data_provider import get_historical_prices
from portfolio_construction_engine import generate_investment_recommendations
from risk_engine import assess_investor_risk_profile
from screening_engine import screen_candidate_securities
from system_administration import get_explanation_rules, get_portfolio_construction_rules

DEFAULT_PLAN_DIRECTORY = Path("saved_plans")


class SessionOutcome(NamedTuple):
    presented_plan: PresentedInvestmentPlan
    saved_plan: SavedInvestmentPlan | None
    confirmation: SavedPlanConfirmation | None


def trace(tag: str, message: str) -> None:
    print(f"[{tag}] {message}")


def run_investment_planning_session(
    *, save_requested: bool = True, plan_store: PlanStore | None = None
) -> SessionOutcome:
    """Run UC.1 once. save_requested=False models an investor who never asks to save."""
    recommendations = _generate_recommendations()
    return _deliver_investment_plan(
        recommendations,
        save_requested=save_requested,
        plan_store=plan_store or JsonPlanStore(DEFAULT_PLAN_DIRECTORY),
    )


def _generate_recommendations() -> InvestmentRecommendationsAndWeights:
    """UC.1.1 to UC.1.15: F.1 to F.5."""
    session_id = initiate_session()
    trace("X.1", f"Initiate Session -> {session_id}")

    investor_profile_and_responses = {
        "financial_profile": request_financial_profile(session_id),
        "risk_questionnaire_responses": provide_risk_questionnaire_response(),
        "current_holdings": provide_current_holdings(),
    }
    trace("F.1 | C.1", "Collect Investor Information -> Investor Profile and Risk Questionnaire Responses")

    risk_assessment = assess_investor_risk_profile(investor_profile_and_responses)
    trace(
        "F.2 | C.2",
        f"Assess Investor Risk Profile -> risk score {risk_assessment['risk_score']}, "
        f"{risk_assessment['risk_category']}",
    )
    present_risk_assessment(risk_assessment)
    confirmed = confirm_profile_interpretation()
    trace("X.1", f"Confirm Profile Interpretation -> {'confirmed' if confirmed else 'not confirmed'}")

    market_data = get_historical_prices(["AAPL", "MSFT", "VTI"], "5y")
    trace("X.2", "Provide Market Data -> Historical Market Data for " + ", ".join(market_data))

    target_allocation = determine_target_asset_allocation(risk_assessment, market_data)
    shares = ", ".join(
        f"{asset_class} {share:.0%}" for asset_class, share in target_allocation["weights"].items()
    )
    trace("F.3 | C.3", f"Determine Target Asset Allocation -> {shares}")

    screened = screen_candidate_securities(target_allocation, market_data)
    trace(
        "F.4 | C.4",
        "Screen Candidate Securities -> " + ", ".join(c["symbol"] for c in screened["candidates"]),
    )

    recommendations = generate_investment_recommendations(
        screened,
        target_asset_allocation=target_allocation,
        portfolio_construction_rules=get_portfolio_construction_rules(),
    )
    trace(
        "F.5 | C.5",
        "Generate Investment Recommendations -> Investment Recommendations and Weights: "
        + ", ".join(f"{r.symbol} {r.weight:.0%}" for r in recommendations.recommendations),
    )
    return recommendations


def _deliver_investment_plan(
    recommendations: InvestmentRecommendationsAndWeights,
    *,
    save_requested: bool,
    plan_store: PlanStore,
) -> SessionOutcome:
    """UC.1.16 to UC.1.20: F.6.1 to F.6.5."""
    explanation_rules = get_explanation_rules()
    explanation = explain_investment_plan(recommendations, explanation_rules=explanation_rules)
    trace(
        "F.6.1 | C.6.1",
        f"Explain Investment Plan -> Investment Plan Explanation, "
        f"{len(explanation.material_risks)} risks explained",
    )

    presented_plan, snapshot = present_investment_plan(
        recommendations, explanation, explanation_rules=explanation_rules
    )
    trace(
        "F.6.2 | C.6.2",
        f"Present Investment Plan -> Presented Investment Plan {presented_plan.plan_id} "
        "and IO.6.1 Reviewed Plan Snapshot",
    )
    view_presented_plan(presented_plan)

    plan_save_request = request_plan_save(presented_plan, wants_to_save=save_requested)
    trace(
        "X.1",
        "Request Plan Save -> "
        + (f"Plan Save Request {plan_save_request.request_id}" if plan_save_request else "no request sent"),
    )

    payload = validate_explicit_plan_save_request(snapshot, plan_save_request=plan_save_request)
    if payload is None:
        problem = plan_save_request_problem(snapshot, plan_save_request)
        trace("F.6.3 | C.6.3", f"Validate Explicit Plan Save Request -> no payload: {problem}")
        trace("F.6.4 | C.6.4", "Persist Reviewed Investment Plan -> not run, nothing is saved")
        trace("F.6.5 | C.6.5", "Confirm Successful Plan Save -> not run, no confirmation is sent")
        return SessionOutcome(presented_plan, None, None)
    trace("F.6.3 | C.6.3", "Validate Explicit Plan Save Request -> IO.6.2 Authorized Plan Save Payload")

    persistence_result = persist_reviewed_investment_plan(
        payload, plan_save_request=plan_save_request, plan_store=plan_store
    )
    trace(
        "F.6.4 | C.6.4",
        f"Persist Reviewed Investment Plan -> IO.6.3 Plan Persistence Result: "
        f"{persistence_result.status}, {persistence_result.detail}",
    )

    confirmed_save = confirm_successful_plan_save(persistence_result, plan_save_request=plan_save_request)
    if confirmed_save is None:
        trace("F.6.5 | C.6.5", "Confirm Successful Plan Save -> no confirmation, the save did not succeed")
        return SessionOutcome(presented_plan, None, None)
    saved_plan, confirmation = confirmed_save
    trace(
        "F.6.5 | C.6.5",
        "Confirm Successful Plan Save -> Saved Investment Plan and Saved Plan Confirmation",
    )

    trace("X.1", "Review Saved Plan")
    review_saved_plan(saved_plan, confirmation)
    return SessionOutcome(presented_plan, saved_plan, confirmation)
