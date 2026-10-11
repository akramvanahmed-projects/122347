"""Human cost of the war price shocks: life-years, healthy life-years, hardship.

Method (transparent, deliberately simple):

1. Cross-sectional gradient. CBS reports Q5 households live `le_gap_years`
   longer than Q1 households. With an income ratio R between them, the
   gradient is  beta = le_gap / ln(R)  years of life per log-point of income.

2. Temporary shock. That gradient reflects a lifetime of income difference.
   A shock lasting d years with relative income loss x is credited
       x * beta * (d / exposure_years) * causal_share
   years of life expectancy per person.

3. Aggregation. Multiply by persons per quintile, sum, and divide by life
   expectancy to express the total as "full lifetimes lost".

This is an order-of-magnitude estimate with an explicit range, NOT a count of
deaths. The dashboard labels it that way.
"""
from __future__ import annotations

import math

import pandas as pd

SCENARIOS = ("low", "central", "high")
DAYS = 365.25


def income_ratio(hh: pd.DataFrame, hc: dict) -> float:
    if hc.get("income_ratio_q5_q1"):
        return float(hc["income_ratio_q5_q1"])
    inc = hh.get("income_eur_year")
    if inc is not None and inc.notna().all() and inc["Q1"] > 0:
        return float(inc["Q5"] / inc["Q1"])
    return 4.5


def life_cost(summary: pd.DataFrame, hh: pd.DataFrame, hc: dict, denom: str = "income") -> pd.DataFrame:
    """Per quintile and scenario: days of (healthy) life lost per person, totals, lifetimes.

    `summary` is model.episode_summary output; both gross and net (after
    compensation) are computed so the dashboard can show lives "saved".
    """
    ln_r = math.log(income_ratio(hh, hc))
    beta_le, beta_hle = hc["le_gap_years"] / ln_r, hc["hle_gap_years"] / ln_r
    years = summary["months"].iloc[0] / 12
    persons_q = hc["households_total"] * hc["persons_per_household"] / len(summary)

    rows = []
    for scen in SCENARIOS:
        cs = hc["causal_share"][scen]
        scale = years / hc["exposure_years"] * cs
        for q, r in summary.iterrows():
            for basis in ("gross", "net"):
                x = max(r[f"{basis}_pct_{denom}"], 0.0) / 100        # average annual share lost
                le = x * beta_le * scale                               # years per person
                hle = x * beta_hle * scale
                rows.append({
                    "scenario": scen, "quintile": q, "basis": basis,
                    "days_le_per_person": le * DAYS,
                    "days_hle_per_person": hle * DAYS,
                    "life_years_total": le * persons_q,
                    "healthy_years_total": hle * persons_q,
                    "persons": persons_q,
                })
    out = pd.DataFrame(rows)
    out["lifetimes_equiv"] = out["life_years_total"] / hc["life_expectancy"]
    return out


def headline(lc: pd.DataFrame) -> pd.DataFrame:
    """Scenario x basis totals across all quintiles."""
    t = lc.groupby(["scenario", "basis"])[["life_years_total", "healthy_years_total", "lifetimes_equiv"]].sum()
    pop = lc.groupby(["scenario", "basis"])["persons"].sum()
    t["days_le_per_person_avg"] = t["life_years_total"] / pop * DAYS
    return t


def hardship(losses: pd.DataFrame, summary: pd.DataFrame, hh: pd.DataFrame, hc: dict,
             prices: pd.DataFrame, survey_year: str = "2020") -> pd.DataFrame:
    """Households whose net war loss exceeds `hardship_food_months` of their own food budget.

    Quintile-level comparison (all households in a quintile share its average),
    so the count moves in steps of one fifth of households.
    """
    yr = prices.loc[prices.index.year == int(survey_year), "all_items"].mean()
    uprate = prices.loc[losses["month"].unique(), "all_items"].mean() / yr
    food_month = hh["share_food"] * hh["spending_eur_year"] / 12 * uprate
    hh_q = hc["households_total"] / len(summary)
    out = pd.DataFrame({
        "net_loss_eur": summary["net_eur"],
        "food_month_eur": food_month,
    })
    out["food_months_lost"] = out["net_loss_eur"] / out["food_month_eur"]
    out["in_hardship"] = out["food_months_lost"] >= hc["hardship_food_months"]
    out["households"] = hh_q * out["in_hardship"]
    out["persons"] = out["households"] * hc["persons_per_household"]
    return out
