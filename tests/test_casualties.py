import pandas as pd
import pytest

from warcost.casualties import cold_deaths, wounded

PARAMS = {
    "adults": 1_000_000, "money_worry_rise_pct": 10, "money_worry_years": 2.0, "war_worry_pct": 50,
    "war_worry_years": 0.5, "food_aid_2021": 100, "food_aid_2022": 150, "food_aid_years": 1.0,
    "missed_support_years": 1.0, "holiday_population": 1_000_000, "holiday_rise_pct": 1.0,
    "cold_home_households": 1000,
    "worry_weight": {"low": 0.005, "central": 0.01, "high": 0.03},
    "hardship_weight": {"low": 0.03, "central": 0.06, "high": 0.133},
}


def test_cold_deaths_are_elasticity_times_gap_times_baseline():
    gap = pd.Series([0.4, 0.6], index=pd.period_range("2022-10", "2022-11", freq="M"))
    params = {"elasticity": {"low": 0.01, "central": 0.03, "high": 0.05}, "heating_season": ["2022-10", "2022-11"],
              "expected_deaths": 10_000, "observed_excess_dec_jan": 0}
    result = cold_deaths(gap, params)
    assert result["deaths"]["central"] == pytest.approx(0.03 * 0.5 * 10_000)
    assert result["season_price_gap_pct"] == pytest.approx(50)


def test_wounded_counts_and_healthy_years():
    groups = {g["group"]: g for g in wounded(PARAMS, q1_households=1000, q1_persons_per_household=2, take_up=0.6)}
    assert groups["Needed food aid"]["people"] == 50
    assert groups["Needed food aid"]["healthy_years"]["central"] == pytest.approx(50 * 0.06)
    assert groups["Poorest fifth without the €1,300 payment"]["people"] == 800
    assert groups["New money worries"]["healthy_years"]["central"] == pytest.approx(100_000 * 0.01 * 2)
    assert groups["Lived in a colder home"]["healthy_years"]["high"] == 0
