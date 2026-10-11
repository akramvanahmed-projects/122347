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
    """Deaths per heating season from the excess heating price. Seasons at or below the
    no-war path count zero: cheaper-than-expected heating is not credited as lives saved."""
    seasons = params.get("heating_seasons") or [params["heating_season"]]
    per_season = []
    for start, end in seasons:
        window = gap.loc[start:end]
        if window.empty:
            continue
        season_gap = float(window.mean())
        counted = max(season_gap, 0.0)
        per_season.append({
            "season": f"{start[:4]}–{end[2:4]}", "months": len(window), "price_gap_pct": season_gap * 100,
            "deaths": {s: params["elasticity"][s] * counted * params["expected_deaths"] * len(window) / 6
                       for s in SCENARIOS},
        })
    deaths = {s: sum(p["deaths"][s] for p in per_season) for s in SCENARIOS}
    return {"season_price_gap_pct": per_season[0]["price_gap_pct"] if per_season else 0.0,
            "seasons": per_season, "deaths": deaths,
            "observed_excess_dec_jan": params["observed_excess_dec_jan"]}


def _yearly_excess(values: dict, base: float, scale: float) -> tuple[float, float, list[str]]:
    """Peak extra people and person-years from yearly levels above a pre-war base.

    Years below the base count zero; years not measured are not in `values` and count zero.
    """
    extra = {year: max(v - base, 0.0) * scale for year, v in values.items()}
    counted = sorted(y for y, v in extra.items() if v > 0)
    return max(extra.values(), default=0.0), sum(extra.values()), counted


def wounded(params: dict, q1_households: float, q1_persons_per_household: float, take_up: float) -> list[dict]:
    """Groups whose quality of life the war damaged, with healthy life-years lost (YLD).

    `people` is the largest number affected in any one year; `person_years` adds
    every year in the window in which the group was measurably larger than before the war.
    """
    adults = params["adults"]
    missed = q1_households * (1 - take_up) * q1_persons_per_household
    food_people, food_py, food_years = _yearly_excess(params["food_aid"], params["food_aid_base"], 1.0)
    worry_people, worry_py, worry_years = _yearly_excess(params["money_worry_pct"], params["money_worry_base_pct"],
                                                         adults / 100)
    hol_people, hol_py, hol_years = _yearly_excess(params["no_holiday_pct"], params["holiday_base_pct"],
                                                   params["holiday_population"] / 100)
    span = lambda ys: ys[0] if len(ys) == 1 else f"{ys[0]}–{ys[-1]}"
    rows = [
        ("Needed food aid", "serious", food_people, food_py, params["hardship_weight"], "partly",
         "years with more people at food banks than in 2021: " + ", ".join(food_years)),
        ("Poorest fifth without the €1,300 payment", "serious", missed, missed * params["missed_support_years"],
         params["worry_weight"], "yes", "Mar 2022 – Dec 2023, the support years"),
        ("New money worries", "light", worry_people, worry_py, params["worry_weight"], "partly",
         f"{span(worry_years)}, compared with 2021"),
        ("Worried a lot about the war", "light", adults * params["war_worry_pct"] / 100,
         adults * params["war_worry_pct"] / 100 * params["war_worry_years"], params["worry_weight"], "yes",
         "Mar – Apr 2022"),
        ("Skipped a holiday", "light", hol_people, hol_py, {s: params["worry_weight"][s] / 2 for s in SCENARIOS},
         "can't tell", f"{span(hol_years)}, compared with 2019"),
        ("Lived in a colder home", "light", params["cold_home_households"] * 2.1,
         params["cold_home_households"] * 2.1 * 0.5, {s: 0.0 for s in SCENARIOS}, "yes", "winter 2022–23"),
    ]
    out = []
    for name, severity, people, person_years, weight, blame, period in rows:
        yld = {s: person_years * weight[s] for s in SCENARIOS}
        out.append({"group": name, "severity": severity, "people": round(people),
                    "years": person_years / people if people else 0.0, "person_years": person_years,
                    "period": period, "weight": weight, "healthy_years": yld, "blame": blame})
    return out


def ledger(cfg: dict, inputs: dict, results: dict[str, EpisodeResult], lives: dict[str, pd.DataFrame],
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
    by_war = {war: {s: float(frame.query("scenario == @s and basis == 'net'")["lifetimes"].sum())
                    for s in SCENARIOS} for war, frame in lives.items()}
    income_lifetimes = {s: sum(w[s] for w in by_war.values()) for s in SCENARIOS}
    wound_lifetimes = {s: sum(g["healthy_years"][s] for g in groups) / life for s in SCENARIOS}
    total_lives = {s: cold["deaths"][s] + income_lifetimes[s] + wound_lifetimes[s] for s in SCENARIOS}
    return {
        "cold": cold,
        "wounded": groups,
        "income_lifetimes": income_lifetimes,
        "income_lifetimes_by_war": by_war,
        "window": {"start": str(min(r.gap.index.min() for r in results.values())),
                   "end": str(max(r.gap.index.max() for r in results.values()))},
        "wound_lifetimes": wound_lifetimes,
        "total_lives": total_lives,
        "attention_lifetimes": attention_lifetimes,
        "serious_wounded": sum(g["people"] for g in groups if g["severity"] == "serious"),
        "light_wounded": sum(g["people"] for g in groups if g["severity"] == "light"),
    }


def attention_lifetimes(facts: dict) -> float:
    """Waking lifetimes of attention: an intense first spring, a first-year background,
    then a lower background for the rest of the window (both wars)."""
    a = facts["attention"]
    followers = a["adults"] * a["followShare"] / 100
    minutes = (a["intenseMinutesDefault"] * a["intenseDays"] + a["backgroundMinutesDefault"] * a["backgroundDays"]
               + a["laterMinutesDefault"] * a["laterDays"])
    return followers * minutes / 60 / (82 * 365.25 * a["wakingHoursPerDay"])
