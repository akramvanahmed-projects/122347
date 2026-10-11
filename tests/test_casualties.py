import pandas as pd
import pytest

from warcost.casualties import cold_deaths, wounded

PARAMS = {
    "adults": 1_000_000, "money_worry_base_pct": 20, "money_worry_pct": {"2022": 30, "2023": 30},
    "war_worry_pct": 50, "war_worry_years": 0.5, "food_aid_base": 100,
    "food_aid": {"2022": 150, "2023": 90, "2024": 120},
    "missed_support_years": 1.0, "holiday_population": 1_000_000, "holiday_base_pct": 10,
    "no_holiday_pct": {"2022": 11},
    "cold_home_households": 1000,
    "worry_weight": {"low": 0.005, "central": 0.01, "high": 0.03},
    "hardship_weight": {"low": 0.03, "central": 0.06, "high": 0.133},
}


def test_cold_deaths_are_elasticity_times_gap_times_baseline():
    gap = pd.Series([0.4, 0.6], index=pd.period_range("2022-10", "2022-11", freq="M"))
    params = {"elasticity": {"low": 0.01, "central": 0.03, "high": 0.05}, "heating_season": ["2022-10", "2022-11"],
              "expected_deaths": 10_000, "observed_excess_dec_jan": 0}
    result = cold_deaths(gap, params)
    # Expected deaths are per six-month season, so a two-month window counts a third.
    assert result["deaths"]["central"] == pytest.approx(0.03 * 0.5 * 10_000 * 2 / 6)
    assert result["season_price_gap_pct"] == pytest.approx(50)


def test_wounded_counts_and_healthy_years():
    groups = {g["group"]: g for g in wounded(PARAMS, q1_households=1000, q1_persons_per_household=2, take_up=0.6)}
    # Peak year 50 extra; 2023 is below the base and counts zero; 2024 adds 20.
    assert groups["Needed food aid"]["people"] == 50
    assert groups["Needed food aid"]["healthy_years"]["central"] == pytest.approx(70 * 0.06)
    assert groups["Poorest fifth without the €1,300 payment"]["people"] == 800
    assert groups["New money worries"]["healthy_years"]["central"] == pytest.approx(100_000 * 0.01 * 2)
    assert groups["Skipped a holiday"]["people"] == 10_000
    assert groups["Lived in a colder home"]["healthy_years"]["high"] == 0


def test_cold_deaths_add_seasons_and_do_not_credit_cheap_winters():
    gap = pd.Series([0.5] * 6 + [-0.2] * 6, index=pd.period_range("2022-10", "2022-10", freq="M").append(
        pd.period_range("2022-11", "2023-09", freq="M")))
    params = {"elasticity": {"low": 0.01, "central": 0.02, "high": 0.05},
              "heating_seasons": [["2022-10", "2023-03"], ["2023-04", "2023-09"]],
              "expected_deaths": 10_000, "observed_excess_dec_jan": 0}
    result = cold_deaths(gap, params)
    assert result["deaths"]["central"] == pytest.approx(0.02 * 0.5 * 10_000)
    assert result["seasons"][1]["deaths"]["central"] == 0


def test_persistent_gap_caps_then_freezes():
    from warcost.prices import persistent_gap
    idx = pd.period_range("2023-10", "2024-03", freq="M")
    gap = pd.DataFrame({"food": [0.1, 0.1, 0.1, 0.2, 0.05, 0.3]}, index=idx)
    out = persistent_gap(gap, "2023-12", "2024-02")
    assert list(out["food"].round(3)) == [0.1, 0.1, 0.1, 0.1, 0.05, 0.05]
