"""F.4 Screen Candidate Securities, performed by C.4 Security Screening Engine.

Satisfies 1.4.4; also 1.1.7 and 1.1.13.

ICOM from the first-level IDEF0 of F.0:
    inputs     Target Asset Allocation (from F.3)
               Historical Market Data (from X.2)
    controls   Market and Regulatory Constraints (from ENV.1)
               Security Screening Criteria (from X.3)
    output     Screened Candidate Securities (to F.5)
    mechanism  C.4 Security Screening Engine

An instrument becomes a candidate only if its asset class is in the target
allocation, it is a permitted product, individual stocks are allowed for the
investor's category, its admitted history is long enough, and its historical
volatility is within the limit for its class. Every rejected instrument is
listed with the reason, so the screen can be explained and checked.
"""

from historical_analysis import annualized_return, annualized_volatility, daily_returns
from model_flows import (
    Candidate,
    Exclusion,
    HistoricalMarketData,
    ScreenedCandidateSecurities,
    TargetAssetAllocation,
)


def screen_candidate_securities(
    target_asset_allocation: TargetAssetAllocation,
    historical_market_data: HistoricalMarketData,
    *,
    market_and_regulatory_constraints: dict,
    security_screening_criteria: dict,
) -> ScreenedCandidateSecurities:
    """Apply the screening criteria to every configured instrument in an allocated asset class."""
    criteria = security_screening_criteria
    category = target_asset_allocation.risk_assessment.risk_category
    order = criteria["category_order"]
    stocks_allowed = order.index(category) >= order.index(criteria["individual_stocks_from_category"])

    candidates, exclusions = [], []
    for symbol, instrument in criteria["instruments"].items():
        asset_class = instrument["asset_class"]
        if target_asset_allocation.weights.get(asset_class, 0) <= 0:
            continue
        reason = _regulatory_reason(instrument, market_and_regulatory_constraints)
        if reason is None and instrument["type"] == "Stock" and not stocks_allowed:
            reason = (
                f"individual stocks are offered from the {criteria['individual_stocks_from_category']} "
                f"category up, and this plan is {category}"
            )
        series = historical_market_data.series.get(symbol)
        if reason is None and series is None:
            reason = "no admitted historical data"
        if reason is None and len(series.dates) < criteria["min_observations"]:
            reason = f"only {len(series.dates)} daily prices, fewer than the {criteria['min_observations']} required"
        if reason is None:
            volatility = annualized_volatility(daily_returns(series.adjusted_closes))
            limit = criteria["max_annualized_volatility"][asset_class]
            if volatility > limit:
                reason = f"historical volatility {volatility:.0%} is above the {limit:.0%} limit for {asset_class}"
        if reason:
            exclusions.append(Exclusion(symbol, reason))
            continue
        candidates.append(
            Candidate(
                symbol=symbol,
                name=instrument["name"],
                asset_class=asset_class,
                instrument_type=instrument["type"],
                observations=len(series.dates),
                annualized_return=annualized_return(series.dates, series.adjusted_closes),
                annualized_volatility=volatility,
                series=series,
            )
        )

    return ScreenedCandidateSecurities(
        candidates=candidates,
        exclusions=exclusions,
        data_limitations=list(historical_market_data.limitations),
        snapshot_id=historical_market_data.snapshot_id,
    )


def _regulatory_reason(instrument: dict, constraints: dict) -> str | None:
    if instrument["type"] not in constraints["allowed_types"]:
        return f"{instrument['type']} products are not permitted"
    if constraints["exclude_leveraged_or_inverse"] and (instrument.get("leveraged") or instrument.get("inverse")):
        return "leveraged and inverse products are not permitted"
    return None
