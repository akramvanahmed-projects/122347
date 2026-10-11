"""Counterfactual price model and distributional loss calculation.

All functions are pure (DataFrame in, DataFrame out) so they are easy to test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

QUINTILES = ["Q1", "Q2", "Q3", "Q4", "Q5"]
SHARE_GROUPS = ["food", "home_energy", "motor_fuel"]
ALL_GROUPS = SHARE_GROUPS + ["core"]


def counterfactual(prices: pd.DataFrame, shock_start: str, method: str = "pre_trend",
                   pre_months: int = 24, target_rate: float = 0.02,
                   floor_rate: float = 0.0) -> pd.DataFrame:
    """No-war price path for every column, anchored on the shock month.

    pre_trend: each group keeps growing at its average annual rate over the
               `pre_months` months up to the anchor month.
    target:    every group grows at `target_rate` per year.
    """
    anchor = pd.Period(shock_start, freq="M")
    if anchor not in prices.index:
        raise ValueError(f"shock month {anchor} not in price data")
    base = prices.loc[anchor]
    months_after = np.array([(m - anchor).n for m in prices.index])
    cf = pd.DataFrame(index=prices.index, columns=prices.columns, dtype=float)
    for col in prices.columns:
        if method == "pre_trend":
            start = anchor - pre_months
            if start not in prices.index:
                raise ValueError(f"need data from {start} for a {pre_months}-month pre-trend")
            annual = (prices.at[anchor, col] / prices.at[start, col]) ** (12 / pre_months) - 1
        elif method == "target":
            annual = target_rate
        else:
            raise ValueError(method)
        annual = max(annual, floor_rate)
        monthly = (1 + annual) ** (1 / 12)
        cf[col] = np.where(months_after >= 0, base[col] * monthly ** months_after, prices[col])
    return cf


def price_gaps(prices: pd.DataFrame, cf: pd.DataFrame, shock_start: str,
               window_end: str | None) -> pd.DataFrame:
    """Excess price level per group, months strictly after the shock month."""
    gap = prices / cf - 1
    start = pd.Period(shock_start, freq="M") + 1
    end = pd.Period(window_end, freq="M") if window_end else gap.index.max()
    return gap.loc[start:end, ALL_GROUPS]


def core_share(hh: pd.DataFrame) -> pd.Series:
    return 1 - hh[[f"share_{g}" for g in SHARE_GROUPS]].sum(axis=1)


def monthly_losses(gaps: pd.DataFrame, hh: pd.DataFrame, prices: pd.DataFrame,
                   survey_year: str = "2020") -> pd.DataFrame:
    """Long table: month x quintile x group with loss as share of spending and in €.

    Laspeyres first-order: loss_share = Σ_g w_qg · gap_g  (no substitution → upper bound).
    € spending is uprated from the survey year with the all-items index.
    """
    yr = prices.loc[prices.index.year == int(survey_year), "all_items"].mean()
    weights = hh[[f"share_{g}" for g in SHARE_GROUPS]].copy()
    weights.columns = SHARE_GROUPS
    weights["core"] = core_share(hh)

    rows = []
    for month, g in gaps.iterrows():
        uprate = prices.at[month, "all_items"] / yr
        for q in hh.index:
            monthly_spend = hh.at[q, "spending_eur_year"] / 12 * uprate
            for grp in ALL_GROUPS:
                share_loss = weights.at[q, grp] * g[grp]
                rows.append((month, q, grp, share_loss, share_loss * monthly_spend))
    return pd.DataFrame(rows, columns=["month", "quintile", "group", "loss_share_spend", "loss_eur"])


def compensation_by_quintile(measures: list[dict], episode: str) -> pd.DataFrame:
    """€ per household per quintile for each compensation measure of an episode."""
    rows = []
    for m in measures:
        if m["episode"] != episode:
            continue
        if "eur_per_household" in m:
            eur = m["eur_per_household"]
        else:
            eur = [m["amount"] * t for t in m["take_up_by_quintile"]]
        for q, v in zip(QUINTILES, eur):
            rows.append((m["name"], q, float(v)))
    return pd.DataFrame(rows, columns=["measure", "quintile", "eur"])


def episode_summary(losses: pd.DataFrame, hh: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    """Per quintile: gross € loss, compensation, net loss, as % of annualised income/spending."""
    n_months = losses["month"].nunique()
    gross = losses.groupby("quintile")["loss_eur"].sum()
    c = comp.groupby("quintile")["eur"].sum().reindex(gross.index, fill_value=0.0)
    out = pd.DataFrame({"gross_eur": gross, "compensation_eur": c})
    out["net_eur"] = out["gross_eur"] - out["compensation_eur"]
    years = n_months / 12
    for denom in ("income", "spending"):
        base = hh[f"{denom}_eur_year"] * years
        out[f"gross_pct_{denom}"] = out["gross_eur"] / base * 100
        out[f"net_pct_{denom}"] = out["net_eur"] / base * 100
    out["months"] = n_months
    out["gross_eur_per_year"] = out["gross_eur"] / years
    return out


def run_episode(prices: pd.DataFrame, hh: pd.DataFrame, cfg: dict, episode: str,
                method: str | None = None, window_end: str | None = "config") -> dict:
    ep = cfg["episodes"][episode]
    cfc = cfg["counterfactual"]
    cf = counterfactual(prices, ep["shock_start"], method or cfc["method"],
                        cfc["pre_trend_months"], cfc["target_rate"], cfc["floor_rate"])
    end = ep["window_end"] if window_end == "config" else window_end
    gaps = price_gaps(prices, cf, ep["shock_start"], end)
    losses = monthly_losses(gaps, hh, prices, cfg["cbs"]["survey_year"])
    comp = compensation_by_quintile(cfg["compensation"], episode)
    return {"cf": cf, "gaps": gaps, "losses": losses, "comp": comp,
            "summary": episode_summary(losses, hh, comp)}
