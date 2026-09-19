from investor_interface import (
    initiate_session, request_financial_profile, provide_risk_questionnaire_response,
    present_risk_score, provide_investment_plan,
)
from risk_engine import determine_risk_score
from market_data_provider import get_historical_prices
from allocation_engine import determine_allocation
from screening_engine import filter_securities
from ai_explanation_model import compose_explanation

def generate_investment_plan() -> dict:
    session_id = initiate_session()
    profile = request_financial_profile(session_id)
    questionnaire = provide_risk_questionnaire_response()
    risk_score = determine_risk_score(profile, questionnaire)
    present_risk_score(risk_score)
    market_data = get_historical_prices(["AAPL", "MSFT", "VTI"], "5y")
    allocation = determine_allocation(risk_score, profile, market_data)
    recommendations = filter_securities(allocation, market_data)
    explanation = compose_explanation(allocation, recommendations)
    provide_investment_plan(allocation, recommendations, explanation)
    return {"risk_score": risk_score, "allocation": allocation, "recommendations": recommendations, "explanation": explanation}