"""Translate income loss into life-years using the Dutch income–longevity gradient.

The gradient (Q5 outlives Q1 by ~8.5 years) is cross-sectional and mostly not
causal: illness lowers income as much as low income causes illness. The model
therefore takes a small, explicit causal share of it and scales it down for a
shock that lasts months rather than a lifetime. Results are equivalences, not
counts of deaths.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import QUINTILES

DAYS_PER_YEAR = 365.25
SCENARIOS = ("low", "central", "high")


def gradient_per_log_income(gap_years: float, income_ratio: float) -> float:
    """Years of life expectancy per unit of log income, from the Q5–Q1 gap."""
    return gap_years / np.log(income_ratio)


def life_cost(summary: pd.DataFrame, population: pd.DataFrame, params: dict,
              income_ratio: float) -> pd.DataFrame:
    """Life and healthy-life days lost per person and in total, per quintile x scenario x basis.

    `population` needs a `persons` column indexed by quintile.
    """
    beta_le = gradient_per_log_income(params["le_gap_years"], income_ratio)
    beta_hle = gradient_per_log_income(params["hle_gap_years"], income_ratio)
    shock_fraction = summary["months"].iloc[0] / 12 / params["exposure_years"]

    frames = []
    for scenario in SCENARIOS:
        scale = shock_fraction * params["causal_share"][scenario]
        for basis in ("gross", "net"):
            # Annual-average income share lost; a net gain is not credited as extra life.
            loss_share = (summary[f"{basis}_pct_income"] / 100).clip(lower=0)
            years_le = -np.log1p(-loss_share) * beta_le * scale
            years_hle = -np.log1p(-loss_share) * beta_hle * scale
            frames.append(pd.DataFrame({
                "scenario": scenario,
                "basis": basis,
                "days_per_person": years_le * DAYS_PER_YEAR,
                "healthy_days_per_person": years_hle * DAYS_PER_YEAR,
                "life_years": years_le * population["persons"],
                "healthy_life_years": years_hle * population["persons"],
                "persons": population["persons"],
            }))
    result = pd.concat(frames).rename_axis("quintile").reset_index()
    result["lifetimes"] = result["life_years"] / params["life_expectancy"]
    return result


def totals(per_quintile: pd.DataFrame) -> pd.DataFrame:
    """Scenario x basis sums across quintiles, plus the population-average days lost."""
    summed = per_quintile.groupby(["scenario", "basis"])[
        ["life_years", "healthy_life_years", "lifetimes", "persons"]
    ].sum()
    summed["days_per_person"] = summed["life_years"] / summed["persons"] * DAYS_PER_YEAR
    return summed.drop(columns="persons")


def grocery_months_lost(summary: pd.DataFrame, households: pd.DataFrame, survey_year: str,
                        price_uprate: float) -> pd.Series:
    """Net war loss per quintile, measured in months of that quintile's own food budget."""
    survey = households.loc[survey_year].loc[QUINTILES]
    monthly_food = survey["share_food"] * survey["spending_eur"] / 12 * price_uprate
    return (summary["net_eur"] / monthly_food).rename("grocery_months")
