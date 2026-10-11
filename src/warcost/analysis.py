"""Run both episodes, the sensitivity grid, and the human-cost layer."""
from __future__ import annotations

import copy
import itertools
import json

import numpy as np
import pandas as pd

from .casualties import attention_lifetimes, ledger
from .config import PROCESSED, QUINTILES, ROOT
from .exposure import EpisodeResult, run_episode
from .health import grocery_months_lost, life_cost, totals
from .sources import load_processed

EPISODES = ("ukraine", "iran")


def load_inputs(cfg: dict) -> dict:
    prices, households, income = load_processed()
    research = pd.read_csv(ROOT / cfg["energy_research_series"], index_col="month")
    return {"prices": prices, "households": households, "income": income, "research_series": research}


def population(income: pd.DataFrame) -> pd.DataFrame:
    latest = income.index.get_level_values("year").max()
    return income.loc[latest].loc[QUINTILES, ["households", "persons"]]


def standardised_income_ratio(income: pd.DataFrame) -> float:
    latest = income.loc[income.index.get_level_values("year").max()]
    return float(latest.at["Q5", "standardised_income_eur"] / latest.at["Q1", "standardised_income_eur"])


def run_all(cfg: dict, inputs: dict, **overrides) -> dict[str, EpisodeResult]:
    return {episode: run_episode(cfg, episode, **inputs, **overrides) for episode in EPISODES}


def support_years(cfg: dict, inputs: dict, **overrides) -> EpisodeResult:
    """The Ukraine episode cut to its acute phase (Mar 2022 - Dec 2023), when support was paid."""
    acute = copy.deepcopy(cfg)
    spec = acute["episodes"]["ukraine"]
    spec["end_month"], spec["freeze_from"] = spec.get("acute_end"), None
    return run_episode(acute, "ukraine", **inputs, **overrides)


def human_cost(cfg: dict, inputs: dict, results: dict[str, EpisodeResult]) -> dict[str, pd.DataFrame]:
    people = population(inputs["income"])
    ratio = standardised_income_ratio(inputs["income"])
    return {
        episode: life_cost(result.summary, people, cfg["human_cost"], ratio)
        for episode, result in results.items()
    }


def sensitivity(cfg: dict, inputs: dict) -> pd.DataFrame:
    """Net loss for Q1 and Q5 (% of income) under every combination of the contested choices."""
    grid = itertools.product(("target", "pre_trend"), (0.0, 0.5, 1.0), ("2020", "2015"))
    rows = []
    for method, energy_weight, survey in grid:
        for episode, result in run_all(cfg, inputs, method=method, energy_weight=energy_weight,
                                       survey_year=survey).items():
            s = result.summary
            rows.append({
                "episode": episode, "counterfactual": method, "energy_correction_weight": energy_weight,
                "survey_year": survey,
                "q1_net_pct": s.at["Q1", "net_pct_income"], "q5_net_pct": s.at["Q5", "net_pct_income"],
                "q1_with_core_pct": s.at["Q1", "net_pct_income"] + s.at["Q1", "core_pct_income"],
                "q5_with_core_pct": s.at["Q5", "net_pct_income"] + s.at["Q5", "core_pct_income"],
            })
    return pd.DataFrame(rows)


def key_numbers(cfg: dict, inputs: dict, results: dict[str, EpisodeResult],
                lives: dict[str, pd.DataFrame]) -> dict:
    """The figures the README and report quote, so prose and data cannot drift apart."""
    out = {"latest_price_month": str(inputs["prices"].index.max())}
    for episode, result in results.items():
        s = result.summary
        t = totals(lives[episode])
        people = population(inputs["income"])
        households_total = people["households"].sum()
        uprate = (inputs["prices"].loc[result.gap.index, "all_items"].mean()
                  / inputs["prices"].loc[inputs["prices"].index.year == int(cfg["cbs"]["survey_year"]),
                                         "all_items"].mean())
        groceries = grocery_months_lost(s, inputs["households"], cfg["cbs"]["survey_year"], uprate)
        out[episode] = {
            "months": int(s["months"].iloc[0]),
            "first_month": str(result.gap.index.min()),
            "last_month": str(result.gap.index.max()),
            "gross_pct_income": s["gross_pct_income"].round(2).to_dict(),
            "net_pct_income": s["net_pct_income"].round(2).to_dict(),
            "core_pct_income": s["core_pct_income"].round(2).to_dict(),
            "gross_eur": s["gross_eur"].round(0).to_dict(),
            "net_eur": s["net_eur"].round(0).to_dict(),
            "compensation_eur": s["compensation_eur"].round(0).to_dict(),
            "national_gross_eur_bn": float((s["gross_eur"] * people["households"]).sum() / 1e9),
            "national_compensation_eur_bn": float((s["compensation_eur"] * people["households"]).sum() / 1e9),
            "grocery_months": groceries.round(2).to_dict(),
            "lifetimes": {f"{sc}_{b}": float(t.at[(sc, b), "lifetimes"])
                          for sc in ("low", "central", "high") for b in ("gross", "net")},
            "life_years_central_net": float(t.at[("central", "net"), "life_years"]),
            "healthy_life_years_central_net": float(t.at[("central", "net"), "healthy_life_years"]),
            "days_per_person_central_net": float(t.at[("central", "net"), "days_per_person"]),
            "households_total": float(households_total),
            "gross_pct_spending": s["gross_pct_spending"].round(2).to_dict(),
            "channel_eur_mean_household": (
                result.losses.groupby("channel")["loss_eur"].sum() / len(QUINTILES)).round(0).to_dict(),
            "q1_break_even_take_up": _break_even_take_up(cfg, episode, s),
            "support_years": _support_summary(cfg, inputs) if episode == "ukraine" else None,
            "peak_energy_gap_pct": float(result.gap["home_energy"].max() * 100),
            "peak_energy_gap_month": str(result.gap["home_energy"].idxmax()),
        }
    out["standardised_income_ratio_q5_q1"] = standardised_income_ratio(inputs["income"])
    return out


def _support_summary(cfg: dict, inputs: dict) -> dict:
    s = support_years(cfg, inputs).summary
    return {"first_month": cfg["window"]["start"], "last_month": cfg["episodes"]["ukraine"]["acute_end"],
            "net_pct_income": s["net_pct_income"].round(2).to_dict(),
            "gross_pct_income": s["gross_pct_income"].round(2).to_dict(),
            "gross_eur": s["gross_eur"].round(0).to_dict(), "net_eur": s["net_eur"].round(0).to_dict(),
            "q1_break_even_take_up": _break_even_take_up(cfg, "ukraine", s)}


def _break_even_take_up(cfg: dict, episode: str, summary: pd.DataFrame) -> float | None:
    """Share of Q1 households that must claim means-tested support for Q1 to break even on average."""
    flat = sum(m["eur_per_household"][0] for m in cfg["compensation"]
               if m["episode"] == episode and "eur_per_household" in m)
    targeted = sum(m["amount"] for m in cfg["compensation"]
                   if m["episode"] == episode and "amount" in m)
    if not targeted:
        return None
    return float(np.clip((summary.at["Q1", "gross_eur"] - flat) / targeted, 0, 1))


def bounds(cfg: dict, inputs: dict) -> dict:
    """Net loss as % of income under the published (0) and recomputed (1) energy series."""
    out = {}
    for weight in (0.0, 1.0):
        for episode, result in run_all(cfg, inputs, energy_weight=weight).items():
            out.setdefault(episode, {})[f"energy_weight_{weight:g}"] = {
                "gross_pct_income": result.summary["gross_pct_income"].round(2).to_dict(),
                "net_pct_income": result.summary["net_pct_income"].round(2).to_dict(),
            }
    return out


def write_outputs(cfg: dict) -> dict:
    inputs = load_inputs(cfg)
    results = run_all(cfg, inputs)
    lives = human_cost(cfg, inputs, results)
    for episode, result in results.items():
        result.summary.to_csv(PROCESSED / f"summary_{episode}.csv")
        lives[episode].to_csv(PROCESSED / f"human_cost_{episode}.csv", index=False)
    sensitivity(cfg, inputs).round(3).to_csv(PROCESSED / "sensitivity.csv", index=False)
    numbers = key_numbers(cfg, inputs, results, lives)
    numbers["energy_bounds"] = bounds(cfg, inputs)
    facts = json.loads((ROOT / "data" / "external" / "story_facts.json").read_text())
    facts["attention"]["laterDays"] = later_attention_days(inputs["prices"].index.max())
    casualty_ledger = ledger(cfg, inputs, results, lives, attention_lifetimes(facts))
    (ROOT / "reports" / "casualties.json").write_text(json.dumps(casualty_ledger, indent=2, default=_jsonable))
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "key_numbers.json").write_text(json.dumps(numbers, indent=2, default=_jsonable))
    return numbers


def later_attention_days(latest_month: pd.Period) -> int:
    """Days from 1 Mar 2023 (after the first war year) to the end of the latest data month."""
    return int((latest_month.end_time.normalize() - pd.Timestamp("2023-03-01")).days) + 1


def _jsonable(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    raise TypeError(type(value))
