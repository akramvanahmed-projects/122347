import math

import pandas as pd
import pytest

from src.human_cost import hardship, headline, life_cost
from tests.test_model import synthetic_households, synthetic_prices

HC = {
    "households_total": 1_000_000, "persons_per_household": 2.0, "life_expectancy": 80.0,
    "le_gap_years": 8.0, "hle_gap_years": 16.0, "income_ratio_q5_q1": math.e ** 2,  # ln R = 2
    "exposure_years": 60, "causal_share": {"low": 0.1, "central": 0.25, "high": 0.5},
    "hardship_food_months": 1.0,
}


def summary(net_pct=3.0, gross_pct=4.0, months=24):
    q = pd.Index(["Q1", "Q2", "Q3", "Q4", "Q5"], name="quintile")
    return pd.DataFrame({"gross_pct_income": gross_pct, "net_pct_income": net_pct,
                         "net_eur": [500, 300, 200, 100, 50], "months": months}, index=q)


def test_days_per_person_formula():
    lc = life_cost(summary(), synthetic_households(), HC)
    row = lc[(lc.scenario == "central") & (lc.basis == "net") & (lc.quintile == "Q1")].iloc[0]
    # 0.03 * (8/2) * (2/60) * 0.25 years
    assert row.days_le_per_person == pytest.approx(0.03 * 4 * (2 / 60) * 0.25 * 365.25)
    assert row.days_hle_per_person == pytest.approx(2 * row.days_le_per_person)


def test_lifetimes_equivalent_and_ordering():
    h = headline(life_cost(summary(), synthetic_households(), HC))
    persons = 2_000_000
    expected_years = 0.03 * 4 * (2 / 60) * 0.25 * persons
    assert h.at[("central", "net"), "life_years_total"] == pytest.approx(expected_years)
    assert h.at[("central", "net"), "lifetimes_equiv"] == pytest.approx(expected_years / 80)
    assert h.at[("low", "net"), "lifetimes_equiv"] < h.at[("central", "net"), "lifetimes_equiv"] \
        < h.at[("high", "net"), "lifetimes_equiv"]
    assert h.at[("central", "gross"), "lifetimes_equiv"] > h.at[("central", "net"), "lifetimes_equiv"]


def test_negative_net_loss_counts_as_zero():
    lc = life_cost(summary(net_pct=-1.0), synthetic_households(), HC)
    assert (lc[lc.basis == "net"]["life_years_total"] == 0).all()


def test_hardship_threshold():
    p, hh = synthetic_prices(), synthetic_households()
    losses = pd.DataFrame({"month": pd.period_range("2022-03", "2022-04", freq="M")})
    s = summary()
    s["net_eur"] = [400, 300, 50, 10, 0]
    out = hardship(losses, s, hh, HC, p)
    # Q1 food per month ≈ 0.15*24000/12 = 300 (×uprate ≈1.03) → 400 > 1 month; Q2: 0.14*30000/12=350 → 300 < 1
    assert out.loc["Q1", "in_hardship"] and not out.loc["Q2", "in_hardship"]
    assert out["households"].sum() == pytest.approx(200_000)
