"""Build the data-driven story page: docs/index.html from docs/story_template.html.

Model outputs are computed here; facts from outside sources live in
data/external/story_facts.json with their citations.
"""
from __future__ import annotations

import json

import pandas as pd

from .analysis import _break_even_take_up, later_attention_days, load_inputs, run_all, support_years
from .config import QUINTILES, ROOT
from .health import totals

DOCS = ROOT / "docs"


def _monthly_mean(result, channel: str, column: str) -> pd.Series:
    losses = result.losses[result.losses["channel"] == channel]
    return losses.groupby("month")[column].mean()


def _phantom_inflation(research: pd.DataFrame) -> list[dict]:
    """Year-on-year CPI inflation, published versus CBS recomputation."""
    index = research.copy()
    index.index = pd.PeriodIndex(index.index, freq="M")
    yoy = (index / index.shift(12) - 1).dropna() * 100
    return [{"m": str(m), "published": round(r.published_index, 1), "actual": round(r.research_index, 1)}
            for m, r in yoy.iterrows()]


def _support_years(cfg: dict, inputs: dict) -> dict:
    """Ukraine result for the support years only (Mar 2022 - Dec 2023), for chapter 04."""
    s = support_years(cfg, inputs).summary
    return {
        "netPct": [round(float(s.at[q, "net_pct_income"]), 2) for q in QUINTILES],
        "grossPct": [round(float(s.at[q, "gross_pct_income"]), 2) for q in QUINTILES],
        "breakEven": round(_break_even_take_up(cfg, "ukraine", s) * 100),
        "q1MissedEur": round(float(s.at["Q1", "gross_eur"]) - 380),
    }


def _window_label(start: str, end: str) -> str:
    a, b = pd.Period(start, freq="M"), pd.Period(end, freq="M")
    return f"{a.strftime('%b %Y')} – {b.strftime('%b %Y')}"


def story_data(cfg: dict) -> dict:
    inputs = load_inputs(cfg)
    results = run_all(cfg, inputs)
    ukraine, iran = results["ukraine"], results["iran"]
    numbers = json.loads((ROOT / "reports" / "key_numbers.json").read_text())
    facts = json.loads((ROOT / "data" / "external" / "story_facts.json").read_text())
    facts["attention"]["laterDays"] = later_attention_days(inputs["prices"].index.max())

    lives = {e: pd.read_csv(ROOT / "data" / "processed" / f"human_cost_{e}.csv") for e in results}
    t_ukr = totals(lives["ukraine"])
    days = float(t_ukr.at[("central", "net"), "days_per_person"])

    food_eur = _monthly_mean(ukraine, "food", "loss_eur")
    food_quarters = food_eur.groupby(food_eur.index.asfreq("Q")).sum()
    acute_end = pd.Period(cfg["episodes"]["ukraine"]["acute_end"], freq="M")
    food_cap = float(ukraine.gap["food"].loc[acute_end - 2:acute_end].mean() * 100)
    casualties = json.loads((ROOT / "reports" / "casualties.json").read_text())
    window = casualties["window"]
    months = (pd.Period(window["end"], freq="M") - pd.Period(window["start"], freq="M")).n + 1
    energy_gap = ukraine.gap["home_energy"] * 100
    iran_fuel_gap = iran.gap["motor_fuel"] * 100
    s = ukraine.summary

    return {
        "asOf": numbers["latest_price_month"],
        "window": {**window, "label": _window_label(window["start"], window["end"]), "months": months,
                   "years": round(months / 12, 1)},
        "facts": facts,
        "ukraine": {
            "householdGross": round(float(s["gross_eur"].mean())),
            "nationalGrossBn": round(numbers["ukraine"]["national_gross_eur_bn"], 1),
            "nationalSupportBn": round(numbers["ukraine"]["national_compensation_eur_bn"], 1),
            "energyGap": [{"m": str(m), "v": round(float(v), 1)} for m, v in energy_gap.items()],
            "peakEnergy": round(float(energy_gap.max())),
            "peakEnergyMonth": str(energy_gap.idxmax()),
            "foodReceipt": [{"q": f"Q{q.quarter} {q.year}", "v": round(float(v), 2)} for q, v in food_quarters.items()],
            "foodMonthly": [{"m": str(m), "v": round(float(v), 2)} for m, v in food_eur.items()],
            "foodTotal": round(float(food_eur.sum())),
            "foodGapEnd": round(food_cap),
            "foodGapActual": round(float((inputs["prices"]["food"] / ukraine.no_war["food"] - 1).iloc[-1] * 100)),
            "supportYears": _support_years(cfg, inputs),
            "netPct": [round(float(s.at[q, "net_pct_income"]), 2) for q in QUINTILES],
            "grossPct": [round(float(s.at[q, "gross_pct_income"]), 2) for q in QUINTILES],
            "netEur": [round(float(s.at[q, "net_eur"])) for q in QUINTILES],

            "hoursPerPerson": round(days * 24, 1),
            "lifetimes": {k: round(v) for k, v in numbers["ukraine"]["lifetimes"].items()},
            "causalCentral": cfg["human_cost"]["causal_share"]["central"],
        },
        "iran": {
            "householdGross": round(float(iran.summary["gross_eur"].mean())),
            "nationalGrossBn": round(numbers["iran"]["national_gross_eur_bn"], 1),
            "nationalSupportBn": round(numbers["iran"]["national_compensation_eur_bn"], 1),
            "fuelGap": [{"m": str(m), "v": round(float(v), 1)} for m, v in iran_fuel_gap.items()],
            "energyGapLast": round(float(iran.gap["home_energy"].iloc[-1] * 100), 1),
            "lifetimes": round(numbers["iran"]["lifetimes"]["central_net"]),
        },
        "casualties": casualties,
        "phantom": _phantom_inflation(inputs["research_series"]),
        "energyPoverty": cfg["indicators"]["energy_poverty_pct"],
        "keptOut": cfg["indicators"]["kept_out_by_support_pct"],
    }


def build_story(cfg: dict) -> None:
    template = (DOCS / "story_template.html").read_text(encoding="utf-8")
    payload = json.dumps(story_data(cfg), ensure_ascii=False, separators=(",", ":"))
    (DOCS / "index.html").write_text(template.replace("/*__DATA__*/null", payload), encoding="utf-8")
