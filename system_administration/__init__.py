"""X.3 System Administrator (stub): the rules WealthPilot runs under.

Explanation Rules control F.6.1 and F.6.2 (over EF.14 and EF.17). Portfolio
Construction Rules control F.5 (over EF.11). Both are fixed fixtures at this
increment.
"""

from investment_plan_management import ExplanationRules


def get_explanation_rules() -> ExplanationRules:
    return ExplanationRules(
        version="ER-1",
        scope_notice="Educational simulation only. No real trade is placed and no money moves.",
        risk_language={
            "market_volatility": (
                "Stock and ETF prices rise and fall. The simulated portfolio can lose value, "
                "especially over short periods."
            ),
            "concentration": (
                "A single company makes up a large part of this plan, so bad news about "
                "that one company can move the whole portfolio."
            ),
        },
        prohibited_phrases=["guaranteed", "risk-free", "order placed", "funds transferred", "buy now"],
        learner_actions=["Save this simulated plan"],
    )


def get_portfolio_construction_rules() -> dict:
    return {"single_stock_limit": 0.25}  # largest share any single stock may take before it is flagged
