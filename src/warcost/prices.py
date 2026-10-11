"""Counterfactual ("no-war") price paths and the excess price gap they imply."""
from __future__ import annotations

import numpy as np
import pandas as pd


def months_since(index: pd.PeriodIndex, anchor: pd.Period) -> np.ndarray:
    return ((index.year - anchor.year) * 12 + (index.month - anchor.month)).to_numpy()


def counterfactual(prices: pd.DataFrame, shock_month: str, method: str = "target",
                   target_rate: float = 0.02, pre_trend_months: int = 24) -> pd.DataFrame:
    """Price level each category would have had without the shock.

    Both methods anchor on the shock month's actual level, so any run-up before
    the war (energy prices rose through late 2021) stays out of the war bill.
    That makes the estimate conservative for Ukraine.
    """
    anchor = pd.Period(shock_month, freq="M")
    if method == "target":
        annual = pd.Series(target_rate, index=prices.columns)
    elif method == "pre_trend":
        start = anchor - pre_trend_months
        annual = ((prices.loc[anchor] / prices.loc[start]) ** (12 / pre_trend_months) - 1).clip(lower=0)
    else:
        raise ValueError(f"unknown counterfactual method: {method}")

    elapsed = months_since(prices.index, anchor)
    growth = np.outer(np.maximum(elapsed, 0), np.log1p(annual.to_numpy()) / 12)
    path = pd.DataFrame(prices.loc[anchor].to_numpy() * np.exp(growth), index=prices.index, columns=prices.columns)
    before_shock = pd.Series(elapsed <= 0, index=prices.index)
    return prices.where(before_shock, path, axis=0)


def excess_gap(prices: pd.DataFrame, no_war: pd.DataFrame, shock_month: str,
               end_month: str | None) -> pd.DataFrame:
    """Actual over counterfactual price level minus one, for months after the shock."""
    start = pd.Period(shock_month, freq="M") + 1
    end = pd.Period(end_month, freq="M") if end_month else prices.index.max()
    return (prices / no_war - 1).loc[start:end]


def persistent_gap(gap: pd.DataFrame, acute_end: str | None, freeze_from: str | None) -> pd.DataFrame:
    """Keep the war's price level after the acute shock without attributing new inflation to it.

    After `acute_end`, each category's excess is capped at its average over the
    last three acute months, so it can only stay or fall. From `freeze_from` on
    (a later shock), it is frozen at its value in that month.
    """
    out = gap.copy()
    if acute_end:
        end = pd.Period(acute_end, freq="M")
        cap = gap.loc[end - 2:end].mean()
        after = out.index > end
        out.loc[after] = out.loc[after].clip(upper=cap, axis=1)
    if freeze_from:
        freeze = pd.Period(freeze_from, freq="M")
        if freeze in out.index:
            later = out.index > freeze
            out.loc[later] = out.loc[freeze].to_numpy()
    return out


def energy_method_correction(research_series: pd.DataFrame, months: pd.PeriodIndex,
                             shock_month: str) -> pd.Series:
    """Correction to the all-items price level from CBS's 2023 energy method change.

    Expressed as a share of the average household's spending, relative to the
    shock month (the counterfactual is anchored there). After the last month in
    the CBS table the old and new methods move together, so the last value holds.
    Negative values mean the published index overstated what households paid.
    """
    ratio = (research_series["research_index"] / research_series["published_index"])
    ratio.index = pd.PeriodIndex(ratio.index, freq="M")
    anchor = pd.Period(shock_month, freq="M")
    if anchor not in ratio.index:
        return pd.Series(0.0, index=months)
    relative = ratio / ratio.loc[anchor] - 1
    return relative.reindex(months.union(relative.index)).ffill().reindex(months).fillna(0.0)
