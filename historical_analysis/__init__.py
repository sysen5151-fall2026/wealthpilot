"""Shared calculations on admitted historical prices (used by F.3, F.4 and F.5).

All results describe the historical sample only. None of them is a forecast.
"""

import math
import statistics
from datetime import date

from model_flows import PriceSeries

TRADING_DAYS_PER_YEAR = 252


def daily_returns(closes: list[float]) -> list[float]:
    return [today / yesterday - 1 for yesterday, today in zip(closes, closes[1:])]


def annualized_return(dates: list[str], values: list[float]) -> float:
    """Compound annual growth rate between the first and last observation."""
    years = (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days / 365.25
    if years <= 0:
        return 0.0
    return (values[-1] / values[0]) ** (1 / years) - 1


def annualized_volatility(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    return statistics.stdev(returns) * math.sqrt(TRADING_DAYS_PER_YEAR)


def mix_value_path(
    series_by_symbol: dict[str, PriceSeries], weights: dict[str, float]
) -> tuple[list[str], list[float]]:
    """Value of 1.0 invested in the weighted mix, rebalanced daily, on the dates all symbols share."""
    common = set.intersection(*(set(series_by_symbol[s].dates) for s in weights))
    dates = sorted(common)
    closes = {}
    for symbol in weights:
        by_date = dict(zip(series_by_symbol[symbol].dates, series_by_symbol[symbol].adjusted_closes))
        closes[symbol] = [by_date[d] for d in dates]
    total_weight = sum(weights.values())
    values = [1.0]
    for i in range(1, len(dates)):
        day_return = sum(
            weight / total_weight * (closes[symbol][i] / closes[symbol][i - 1] - 1)
            for symbol, weight in weights.items()
        )
        values.append(values[-1] * (1 + day_return))
    return dates, values


def worst_one_year_return(values: list[float]) -> float | None:
    """Worst return over any window of one trading year, or None if the sample is shorter."""
    window = TRADING_DAYS_PER_YEAR
    if len(values) <= window:
        return None
    return min(values[i] / values[i - window] - 1 for i in range(window, len(values)))
