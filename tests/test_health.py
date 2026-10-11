import math

import pandas as pd
import pytest

from warcost.health import life_cost, totals

PARAMS = {"life_expectancy": 80.0, "le_gap_years": 8.0, "hle_gap_years": 16.0, "exposure_years": 60,
          "causal_share": {"low": 0.1, "central": 0.25, "high": 0.5}}
QUINTILES = ["Q1", "Q2", "Q3", "Q4", "Q5"]


def summary(net_pct: float = 3.0, gross_pct: float = 4.0, months: int = 24) -> pd.DataFrame:
    return pd.DataFrame({"gross_pct_income": gross_pct, "net_pct_income": net_pct, "months": months},
                        index=pd.Index(QUINTILES, name="quintile"))


POPULATION = pd.DataFrame({"persons": 400_000}, index=QUINTILES)


def test_days_per_person():
    result = life_cost(summary(), POPULATION, PARAMS, income_ratio=math.e ** 2)
    row = result.query("scenario == 'central' and basis == 'net' and quintile == 'Q1'").iloc[0]
    expected_years = -math.log(1 - 0.03) * (8 / 2) * (2 / 60) * 0.25
    assert row.days_per_person == pytest.approx(expected_years * 365.25)
    assert row.healthy_days_per_person == pytest.approx(2 * row.days_per_person)


def test_lifetimes_scale_with_population_and_scenarios():
    t = totals(life_cost(summary(), POPULATION, PARAMS, income_ratio=math.e ** 2))
    expected = -math.log(1 - 0.03) * 4 * (2 / 60) * 0.25 * 2_000_000 / 80
    assert t.at[("central", "net"), "lifetimes"] == pytest.approx(expected)
    assert t.at[("low", "net"), "lifetimes"] < t.at[("central", "net"), "lifetimes"] < t.at[("high", "net"), "lifetimes"]
    assert t.at[("central", "gross"), "lifetimes"] > t.at[("central", "net"), "lifetimes"]


def test_net_gain_is_not_counted_as_extra_life():
    result = life_cost(summary(net_pct=-1.0), POPULATION, PARAMS, income_ratio=4.0)
    assert (result.query("basis == 'net'")["life_years"] == 0).all()
