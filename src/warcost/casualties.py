"""The casualty ledger: estimated deaths, the wounded, and lifetimes of lost time.

Three kinds of loss are kept apart because they are different things:
deaths (people), life-year equivalents (expectancy spread thinly across many
people) and waking time. The ledger reports each with a range.
"""
from __future__ import annotations

import pandas as pd

from .exposure import EpisodeResult, spending_weights
from .prices import energy_method_correction

SCENARIOS = ("low", "central", "high")
WAKING_LIFETIME_HOURS = 82 * 365.25 * 16


def heating_price_gap(result: EpisodeResult, households: pd.DataFrame, research: pd.DataFrame,
                      cfg: dict) -> pd.Series:
    """Excess home-energy price by month, with the same midpoint correction the cost model uses.

    The CBS correction is a share of average spending; dividing by the average
    household's energy weight turns it back into a price gap.
    """
    weight = cfg["energy_correction_weight"]
    w_energy = spending_weights(households, cfg["cbs"]["survey_year"]).at["all", "home_energy"]
    correction = energy_method_correction(research, result.gap.index, cfg["episodes"]["ukraine"]["shock_month"])
    return result.gap["home_energy"] + weight * correction / w_energy


def cold_deaths(gap: pd.Series, params: dict) -> dict:
    start, end = params["heating_season"]
    season_gap = float(gap.loc[start:end].mean())
    deaths = {s: params["elasticity"][s] * season_gap * params["expected_deaths"] for s in SCENARIOS}
    return {"season_price_gap_pct": season_gap * 100, "deaths": deaths,
            "observed_excess_dec_jan": params["observed_excess_dec_jan"]}


def wounded(params: dict, q1_households: float, q1_persons_per_household: float, take_up: float) -> list[dict]:
    """Groups whose quality of life the war damaged, with healthy life-years lost (YLD)."""
    adults = params["adults"]
    missed = q1_households * (1 - take_up) * q1_persons_per_household
    rows = [
        ("Needed food aid", "serious", params["food_aid_2022"] - params["food_aid_2021"],
         params["hardship_weight"], params["food_aid_years"], "partly"),
        ("Poorest fifth without the €1,300 payment", "serious", missed,
         params["worry_weight"], params["missed_support_years"], "yes"),
        ("New money worries", "light", adults * params["money_worry_rise_pct"] / 100,
         params["worry_weight"], params["money_worry_years"], "partly"),
        ("Worried a lot about the war", "light", adults * params["war_worry_pct"] / 100,
         params["worry_weight"], params["war_worry_years"], "yes"),
        ("Skipped a holiday", "light", params["holiday_population"] * params["holiday_rise_pct"] / 100,
         {s: params["worry_weight"][s] / 2 for s in SCENARIOS}, 1.0, "can't tell"),
        ("Lived in a colder home", "light", params["cold_home_households"] * 2.1,
         {s: 0.0 for s in SCENARIOS}, 0.5, "yes"),
    ]
    out = []
    for name, severity, people, weight, years, blame in rows:
        yld = {s: people * weight[s] * years for s in SCENARIOS}
        out.append({"group": name, "severity": severity, "people": round(people), "years": years,
                    "weight": weight, "healthy_years": yld, "blame": blame})
    return out


def ledger(cfg: dict, inputs: dict, results: dict[str, EpisodeResult], lives: pd.DataFrame,
           attention_lifetimes: float) -> dict:
    params = cfg["casualties"]
    ukraine = results["ukraine"]
    gap = heating_price_gap(ukraine, inputs["households"], inputs["research_series"], cfg)
    cold = cold_deaths(gap, params["cold"])

    latest = inputs["income"].loc[inputs["income"].index.get_level_values("year").max()]
    q1 = latest.loc["Q1"]
    take_up = next(m["take_up_by_quintile"][0] for m in cfg["compensation"] if "take_up_by_quintile" in m)
    groups = wounded(params["wounded"], q1["households"], q1["persons"] / q1["households"], take_up)

    life = cfg["human_cost"]["life_expectancy"]
    income_lifetimes = {s: float(lives.query("scenario == @s and basis == 'net'")["lifetimes"].sum())
                        for s in SCENARIOS}
    wound_lifetimes = {s: sum(g["healthy_years"][s] for g in groups) / life for s in SCENARIOS}
    total_lives = {s: cold["deaths"][s] + income_lifetimes[s] + wound_lifetimes[s] for s in SCENARIOS}
    return {
        "cold": cold,
        "wounded": groups,
        "income_lifetimes": income_lifetimes,
        "wound_lifetimes": wound_lifetimes,
        "total_lives": total_lives,
        "attention_lifetimes": attention_lifetimes,
        "serious_wounded": sum(g["people"] for g in groups if g["severity"] == "serious"),
        "light_wounded": sum(g["people"] for g in groups if g["severity"] == "light"),
    }


def attention_lifetimes(facts: dict) -> float:
    a = facts["attention"]
    followers = a["adults"] * a["followShare"] / 100
    minutes = a["intenseMinutesDefault"] * a["intenseDays"] + a["backgroundMinutesDefault"] * a["backgroundDays"]
    return followers * minutes / 60 / (82 * 365.25 * a["wakingHoursPerDay"])
