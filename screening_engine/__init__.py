"""F.4 Screen Candidate Securities, performed by C.4 Security Screening Engine (stub).

Inputs Target Asset Allocation (from F.3) and Historical Market Data (from X.2);
output Screened Candidate Securities (to F.5). Weights are set later, by F.5.
"""

ASSET_CLASS_BY_SYMBOL = {"AAPL": "Stocks", "MSFT": "Stocks", "VTI": "ETFs"}


def screen_candidate_securities(
    target_asset_allocation: dict, historical_market_data: dict
) -> dict:
    """Keep the symbols that have price history and belong to an allocated asset class."""
    allocated = target_asset_allocation["weights"]
    candidates = [
        {"symbol": symbol, "asset_class": ASSET_CLASS_BY_SYMBOL[symbol]}
        for symbol, prices in historical_market_data.items()
        if prices and ASSET_CLASS_BY_SYMBOL.get(symbol) in allocated
    ]
    return {
        "candidates": candidates,
        "data_limitations": ["Prices come from a fixed historical sample, not live market data."],
    }
