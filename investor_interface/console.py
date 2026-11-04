"""Console side of C.1 Investor Information Interface: a sample X.1 Individual Investor.

The browser front end is the real way an investor answers the Requests for
Investor Input. This module answers them with a fixed, hypothetical investor
so UC.1 can run in a terminal (python app.py) and in tests, and prints what
the investor would see.
"""

SAMPLE_INVESTOR = {
    "financial_profile": {
        "age": 34,
        "annual_income": 85000,
        "investable_savings": 25000,
        "monthly_contribution": 500,
        "horizon_years": 25,
        "goal": "retirement",
        "liquidity_needs": "low",
    },
    "risk_questionnaire_responses": {
        "drop_reaction": "hold",
        "experience": "a_little",
        "max_loss": "loss_20",
        "objective": "balanced",
        "income_stability": "somewhat_stable",
    },
    "current_holdings": [{"symbol": "VTI", "value": 5000}],
}


def show_risk_assessment(risk) -> None:
    print(f"\nYour risk score is {risk.risk_score} of 100: {risk.risk_category}.")
    for factor in risk.strongest_factors():
        print(f"  {factor.label}: {factor.answer}")


def show_presented_plan(presented_plan) -> None:
    print()
    print(presented_plan.display_text)
    print()


def show_saved_plan(saved_plan, confirmation) -> None:
    print(confirmation.message)
    print(f"Saved plan {saved_plan.plan_id}: {len(saved_plan.content['recommendations'])} securities.")


def show_withheld(reason: str, limitations: list[str]) -> None:
    print(f"\nThe plan was withheld: {reason}")
    for line in limitations:
        print(f"  - {line}")
