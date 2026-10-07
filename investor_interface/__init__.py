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


def present_risk_assessment(risk_score: int) -> None:
    print("SIMULATED EDUCATIONAL OUTPUT")
    print(f"Risk score: {risk_score}")


def confirm_profile_interpretation() -> bool:
    confirmed = True
    print("Profile interpretation confirmed:", confirmed)
    return confirmed


def provide_investment_plan(
    allocation: dict,
    candidates: list,
    explanation: str,
) -> None:
    print("SIMULATED EDUCATIONAL PLAN")
    print("Allocation:", allocation)
    print("Candidate securities:", candidates)
    print("Explanation:", explanation)


def request_plan_save() -> bool:
    requested = True
    print("Plan save requested:", requested)
    return requested
