import numpy as np
import pandas as pd
import pytest

from warcost.exposure import compensation, run_episode, spending_weights
from warcost.prices import counterfactual, energy_method_correction, excess_gap


def test_target_counterfactual_isolates_the_jump(prices):
    no_war = counterfactual(prices, "2022-02", "target", 0.02)
    gap = excess_gap(prices, no_war, "2022-02", "2023-12")
    assert np.allclose(gap["home_energy"], 0.5)
    assert np.allclose(gap[["food", "motor_fuel", "core"]], 0.0)
    assert gap.index.min() == pd.Period("2022-03", "M")


def test_pre_trend_recovers_steady_growth(prices):
    no_war = counterfactual(prices, "2022-02", "pre_trend", pre_trend_months=24)
    assert np.allclose(no_war["food"], prices["food"])


def test_imputed_rent_is_removed_from_weights(households):
    weights = spending_weights(households, "2020")
    assert weights.at["Q5", "home_energy"] == pytest.approx(0.04 / 0.80)
    assert np.allclose(weights.sum(axis=1), 1.0)


def test_compensation_take_up():
    measures = [{"name": "flat", "episode": "x", "eur_per_household": [100] * 5},
                {"name": "targeted", "episode": "x", "amount": 1000, "take_up_by_quintile": [0.5, 0, 0, 0, 0]},
                {"name": "other", "episode": "y", "eur_per_household": [999] * 5}]
    total = compensation(measures, "x").groupby("quintile")["eur"].sum()
    assert total["Q1"] == 600 and total["Q5"] == 100


def test_episode_losses_match_hand_calculation(cfg, prices, households, income):
    cfg["episodes"]["ukraine"]["end_month"] = "2022-03"
    result = run_episode(cfg, "ukraine", prices, households, income, energy_method="published")
    q1_energy = result.losses.query("quintile == 'Q1' and channel == 'home_energy'")["loss_eur"].iloc[0]
    uprate = prices.at[pd.Period("2022-03", "M"), "all_items"] / prices.loc["2020-01":"2020-12", "all_items"].mean()
    assert q1_energy == pytest.approx(0.5 * 0.08 * 24000 / 12 * uprate)
    summary = result.summary
    assert summary.at["Q1", "gross_pct_income"] > summary.at["Q5", "gross_pct_income"]
    assert summary.at["Q1", "net_eur"] == pytest.approx(summary.at["Q1", "gross_eur"] - 380 - 2 * 715)


def test_energy_correction_is_relative_to_shock_month():
    series = pd.DataFrame({"published_index": [100.0, 110.0, 120.0], "research_index": [99.0, 104.5, 120.0]},
                          index=["2022-02", "2022-03", "2022-04"])
    months = pd.period_range("2022-03", "2022-06", freq="M")
    correction = energy_method_correction(series, months, "2022-02")
    assert correction.iloc[0] == pytest.approx((104.5 / 110) / 0.99 - 1)
    assert correction.iloc[-1] == correction.iloc[1]          # held after the table ends


def test_energy_correction_is_zero_outside_table():
    series = pd.DataFrame({"published_index": [100.0], "research_index": [95.0]}, index=["2022-02"])
    months = pd.period_range("2026-03", "2026-05", freq="M")
    assert (energy_method_correction(series, months, "2026-02") == 0).all()


def test_income_after_last_cbs_year_is_uprated(cfg, prices, households, income):
    result = run_episode(cfg, "iran", prices, households, income)
    months = result.gap.index
    assert result.summary.at["Q1", "income_eur"] > 20000 / 12 * len(months)
