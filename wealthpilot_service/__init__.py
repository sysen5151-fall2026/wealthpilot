from investor_interface import (
    initiate_session,
    request_financial_profile,
    provide_risk_questionnaire_response,
    provide_current_holdings,
    present_risk_assessment,
    confirm_profile_interpretation,
    provide_investment_plan,
    request_plan_save,
)
from risk_engine import determine_risk_score
from market_data_provider import get_historical_prices
from allocation_engine import determine_allocation
from screening_engine import filter_securities
from ai_explanation_model import compose_explanation


def save_plan_and_confirm(session_id: str, plan: dict) -> dict:
    saved_plan = {
        "session_id": session_id,
        **plan,
        "status": "saved",
    }
    print("Simulated plan saved:", saved_plan)
    return saved_plan


def generate_investment_plan() -> dict:
    session_id = initiate_session()

    profile = request_financial_profile(session_id)
    questionnaire = provide_risk_questionnaire_response()
    holdings = provide_current_holdings()

    risk_score = determine_risk_score(profile, questionnaire)
    present_risk_assessment(risk_score)
    confirm_profile_interpretation()

    market_data = get_historical_prices(["AAPL", "MSFT", "VTI"], "5y")
    allocation = determine_allocation(risk_score, profile, market_data)
    candidates = filter_securities(allocation, market_data)
    explanation = compose_explanation(allocation, candidates)

    provide_investment_plan(allocation, candidates, explanation)
    request_plan_save()

    plan = {
        "risk_score": risk_score,
        "holdings": holdings,
        "allocation": allocation,
        "candidate_securities": candidates,
        "explanation": explanation,
    }

    return save_plan_and_confirm(session_id, plan)
