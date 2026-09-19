def initiate_session() -> str:
    return "session-001"

def request_financial_profile(session_id: str) -> dict:
    return {"age": 30, "income": 80000, "savings": 20000, "goal": "retirement", "horizon_years": 20, "liquidity_needs": "low"}

def provide_risk_questionnaire_response() -> dict:
    return {"risk_tolerance": 3, "risk_capacity": 4, "experience": "beginner", "max_loss": 0.2}

def present_risk_score(risk_score: int) -> None:
    print(f"Risk score: {risk_score}")

def provide_investment_plan(allocation: dict, recommendations: list, explanation: str) -> None:
    print("Allocation:", allocation)
    print("Recommendations:", recommendations)
    print("Explanation:", explanation)