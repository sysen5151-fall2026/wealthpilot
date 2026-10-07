from investor_interface import (
    initiate_session,
    request_financial_profile,
    provide_risk_questionnaire_response,
    present_risk_score,
    confirm_risk_score,
    provide_investment_plan,
    confirm_investment_plan,
)
from risk_engine import determine_risk_score
from market_data_provider import get_historical_prices
from allocation_engine import determine_allocation
from screening_engine import filter_securities
from ai_explanation_model import compose_explanation


def save_investment_plan(session_id: str, plan: dict) -> dict:
    saved_plan = {
        "session_id": session_id,
        **plan,
        "status": "saved",
    }
    print("Plan saved:", saved_plan)
    return saved_plan


def generate_investment_plan() -> dict:
    session_id = initiate_session()

    profile = request_financial_profile(session_id)
    questionnaire = provide_risk_questionnaire_response()

    risk_score = determine_risk_score(profile, questionnaire)
    present_risk_score(risk_score)

    risk_confirmed = confirm_risk_score(risk_score)
    if not risk_confirmed:
        return {"status": "risk_score_not_confirmed"}

    market_data = get_historical_prices(["AAPL", "MSFT", "VTI"], "5y")
    allocation = determine_allocation(risk_score, profile, market_data)
    recommendations = filter_securities(allocation, market_data)
    explanation = compose_explanation(allocation, recommendations)

    provide_investment_plan(allocation, recommendations, explanation)

    plan_confirmed = confirm_investment_plan()
    if not plan_confirmed:
        return {"status": "plan_not_confirmed"}

    plan = {
        "risk_score": risk_score,
        "allocation": allocation,
        "recommendations": recommendations,
        "explanation": explanation,
    }

    return save_investment_plan(session_id, plan)
