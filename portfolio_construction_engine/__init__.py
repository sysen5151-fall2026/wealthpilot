"""F.5 Generate Investment Recommendations, performed by C.5 Portfolio Construction Engine.

Satisfies 1.4.5.

ICOM from the first-level IDEF0 of F.0:
    input      Screened Candidate Securities (from F.4)
    controls   Target Asset Allocation (from F.3)
               Portfolio Construction Rules (from X.3, over EF.11)
    output     Investment Recommendations and Weights (to F.6, over IF.6)
    mechanism  C.5 Portfolio Construction Engine
"""

from investment_plan_management import InvestmentRecommendationsAndWeights, Recommendation


def generate_investment_recommendations(
    screened_candidate_securities: dict,
    *,
    target_asset_allocation: dict,
    portfolio_construction_rules: dict,
) -> InvestmentRecommendationsAndWeights:
    """Weight the screened candidates so each asset class gets its target share.

    Candidates in the same asset class share that class's weight equally.
    """
    candidates = screened_candidate_securities["candidates"]
    recommendations = []
    for asset_class, share in target_asset_allocation["weights"].items():
        symbols = [c["symbol"] for c in candidates if c["asset_class"] == asset_class]
        if not symbols:
            raise ValueError(f"no screened candidate for {asset_class}")
        recommendations += [Recommendation(symbol, asset_class, share / len(symbols)) for symbol in symbols]

    return InvestmentRecommendationsAndWeights(
        risk_score=target_asset_allocation["risk_score"],
        risk_category=target_asset_allocation["risk_category"],
        target_allocation=dict(target_asset_allocation["weights"]),
        recommendations=recommendations,
        identified_risks=_identify_risks(recommendations, portfolio_construction_rules),
        data_limitations=list(screened_candidate_securities["data_limitations"]),
    )


def _identify_risks(recommendations: list[Recommendation], rules: dict) -> list[str]:
    risks = ["market_volatility"] if recommendations else []
    if any(r.asset_class == "Stocks" and r.weight > rules["single_stock_limit"] for r in recommendations):
        risks.append("concentration")
    return risks
