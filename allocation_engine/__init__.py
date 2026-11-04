"""F.3 Determine Target Asset Allocation, performed by C.3 Asset Allocation Engine (stub).

Inputs Risk Score and Risk Category (from F.2) and Historical Market Data
(from X.2); output Target Asset Allocation (to F.4 and F.5).
"""


def determine_target_asset_allocation(
    risk_score_and_category: dict, historical_market_data: dict
) -> dict:
    """Return the Target Asset Allocation with the risk assessment it is based on.

    The 60/40 split is hard-coded at this increment.
    """
    return {**risk_score_and_category, "weights": {"Stocks": 0.6, "ETFs": 0.4}}
