"""F.3 Determine Target Asset Allocation, performed by C.3 Asset Allocation Engine.

Satisfies 1.4.3; also 1.1.1, 1.1.6, 1.1.10 and 1.2.2.

ICOM from the first-level IDEF0 of F.0:
    inputs     Risk Score and Risk Category (from F.2)
               Historical Market Data (from X.2)
    controls   Allocation Rules (from X.3)
               Investment Planning Constraints (from X.3)
               Profile Interpretation Confirmation (from X.1)
    outputs    Target Asset Allocation (to F.4 and F.5)
               Market Data Request (to X.2)
    mechanism  C.3 Asset Allocation Engine

The Allocation Rules give a starting mix for each risk category. Three
Investment Planning Constraints can then change it, each leaving a note that
F.6.1 explains: a short horizon caps stocks, a likely early need keeps a
minimum in cash, and the loss-tolerance check moves money from stocks to bonds
while the mix's worst historical one-year result exceeds the investor's limit.
The check measures each asset class by its benchmark fund, moves at most
loss_tolerance_max_shift, and stops when a further move would cut the
historical loss by less than loss_tolerance_min_improvement (in 2022, for
example, bonds fell almost as much as stocks). If the limit is still exceeded,
the mix is kept as it stands, a note says why, and the plan carries that risk.
"""

from historical_analysis import mix_value_path, worst_one_year_return
from model_flows import HistoricalMarketData, MarketDataRequest, RiskScoreAndCategory, TargetAssetAllocation

PRECISION = 4


def request_historical_market_data(
    risk_score_and_category: RiskScoreAndCategory, *, allocation_rules: dict
) -> MarketDataRequest:
    """Market Data Request: every instrument in the asset classes this category uses."""
    mix = allocation_rules["by_category"][risk_score_and_category.risk_category]
    symbols = []
    for asset_class, definition in allocation_rules["asset_classes"].items():
        if mix[asset_class] > 0:
            for symbol in [definition["benchmark"], *definition["instruments"]]:
                if symbol not in symbols:
                    symbols.append(symbol)
    return MarketDataRequest(symbols=symbols)


def determine_target_asset_allocation(
    risk_score_and_category: RiskScoreAndCategory,
    historical_market_data: HistoricalMarketData,
    *,
    allocation_rules: dict,
    investment_planning_constraints: dict,
    profile_interpretation_confirmed: bool,
) -> TargetAssetAllocation:
    """Start from the category's mix and apply the planning constraints.

    Raises ValueError if the investor has not confirmed the risk assessment.
    """
    if not profile_interpretation_confirmed:
        raise ValueError("the investor has not confirmed the profile interpretation")
    risk = risk_score_and_category
    basis = risk.profile_basis
    constraints = investment_planning_constraints
    classes = allocation_rules["asset_classes"]
    equity = [c for c, d in classes.items() if d["equity"]]
    cash, defensive = allocation_rules["cash_class"], allocation_rules["defensive_class"]

    base = dict(allocation_rules["by_category"][risk.risk_category])
    weights = dict(base)
    adjustments, limitations, flags = [], [], []

    horizon, cap = basis["horizon_years"], constraints["short_horizon_max_equity"]
    if horizon < constraints["short_horizon_years"]:
        flags.append("short_horizon")
        stock_share = sum(weights[c] for c in equity)
        if stock_share > cap:
            _shift(weights, equity, [c for c in classes if c not in equity], stock_share - cap)
            adjustments.append(
                f"You need the money in {horizon} year{'' if horizon == 1 else 's'}, so stocks were capped "
                f"at {cap:.0%} instead of {stock_share:.0%}."
            )

    min_cash = constraints["min_cash_by_liquidity"][basis["liquidity_needs"]]
    if weights[cash] < min_cash:
        shortfall = min_cash - weights[cash]
        _shift(weights, [c for c in classes if c != cash], [cash], shortfall)
        adjustments.append(f"Because you may need this money early, {min_cash:.0%} is kept in cash.")

    if constraints["loss_tolerance_check"]:
        _apply_loss_tolerance(
            weights, risk, historical_market_data, classes, equity, defensive, allocation_rules,
            adjustments, limitations, flags,
        )

    return TargetAssetAllocation(
        weights=_rounded(weights),
        base_weights=base,
        adjustments=adjustments,
        risk_assessment=risk,
        limitations=limitations,
        planning_flags=flags,
    )


def _apply_loss_tolerance(weights, risk, data, classes, equity, defensive, rules, adjustments, limitations, flags):
    benchmarks = {c: classes[c]["benchmark"] for c, w in weights.items() if w > 0 or c == defensive}
    missing = sorted(b for b in benchmarks.values() if b not in data.series)
    if missing:
        limitations.append(
            f"The loss-tolerance check was skipped because there is no admitted data for {', '.join(missing)}."
        )
        return

    def worst(mix: dict) -> float | None:
        active = {benchmarks[c]: w for c, w in mix.items() if w > 0}
        return worst_one_year_return(mix_value_path(data.series, active)[1])

    limit, step, max_shift = risk.max_one_year_loss, rules["loss_tolerance_step"], rules["loss_tolerance_max_shift"]
    original = current = worst(weights)
    if current is None:
        limitations.append("The historical sample is shorter than one year, so the loss-tolerance check was not made.")
        return
    if current >= -limit:
        return
    moved = 0.0
    while current < -limit and moved < max_shift - 1e-9 and sum(weights[c] for c in equity) > 1e-9:
        trial = dict(weights)
        amount = _shift(trial, equity, [defensive], min(step, max_shift - moved))
        result = worst(trial)
        if result - current < rules["loss_tolerance_min_improvement"]:
            break  # moving more would hardly reduce the historical loss
        weights.update(trial)
        moved, current = moved + amount, result

    found = (
        f"In the historical sample the starting mix lost up to {-original:.0%} in one year, more than "
        f"the {limit:.0%} you said you could accept"
    )
    if not moved:
        adjustments.append(
            f"{found}. Moving money from stocks to {defensive.lower()} would hardly have reduced that loss in this "
            "sample, so the mix was kept and the risk is listed with the plan."
        )
    else:
        most = ", the most the rules allow," if moved >= max_shift - 1e-9 else ""
        note = (
            f"{found}, so {moved:.0%}{most} was moved from stocks to {defensive.lower()}; "
            f"the adjusted mix's worst one-year loss was {-current:.0%}."
        )
        if current < -limit:
            note += " That is still above your limit, so the risk is listed with the plan."
        adjustments.append(note)
    if current < -limit:
        flags.append("loss_tolerance")


def _shift(weights: dict, sources: list[str], targets: list[str], amount: float) -> float:
    """Move up to `amount` from the sources to the targets, in proportion to their weights."""
    available = sum(weights[s] for s in sources)
    amount = min(amount, available)
    if amount <= 0:
        return 0.0
    for source in sources:
        weights[source] -= amount * weights[source] / available
    target_total = sum(weights[t] for t in targets)
    for target in targets:
        share = weights[target] / target_total if target_total > 0 else 1 / len(targets)
        weights[target] += amount * share
    return amount


def _rounded(weights: dict) -> dict:
    rounded = {c: round(max(w, 0.0), PRECISION) for c, w in weights.items()}
    largest = max(rounded, key=rounded.get)
    rounded[largest] = round(rounded[largest] + 1 - sum(rounded.values()), PRECISION)
    return rounded
