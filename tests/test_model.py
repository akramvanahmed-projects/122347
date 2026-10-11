"""Model checks on a SYNTHETIC fixture with a known answer (not real data)."""
import numpy as np
import pandas as pd
import pytest

from src.fetch import parse_jsonstat
from src.model import counterfactual, monthly_losses, price_gaps, run_episode

MONTHS = pd.period_range("2018-01", "2026-08", freq="M")
GROUPS = ["food", "home_energy", "motor_fuel", "core", "all_items"]


def synthetic_prices(jump=0.5, shock="2022-02"):
    t = np.arange(len(MONTHS))
    base = 100 * 1.02 ** (t / 12)
    df = pd.DataFrame({g: base for g in GROUPS}, index=MONTHS)
    after = MONTHS > pd.Period(shock, "M")
    df.loc[after, "home_energy"] *= 1 + jump
    return df


def synthetic_households():
    return pd.DataFrame({
        "share_food": [0.15, 0.14, 0.13, 0.12, 0.10],
        "share_home_energy": [0.10, 0.08, 0.06, 0.05, 0.04],
        "share_motor_fuel": [0.03, 0.04, 0.04, 0.05, 0.05],
        "spending_eur_year": [24000, 30000, 36000, 42000, 54000],
        "income_eur_year": [22000, 32000, 42000, 55000, 90000],
    }, index=pd.Index(["Q1", "Q2", "Q3", "Q4", "Q5"], name="quintile"))


def test_target_counterfactual_matches_trend_exactly():
    p = synthetic_prices()
    cf = counterfactual(p, "2022-02", method="target", target_rate=0.02)
    gaps = price_gaps(p, cf, "2022-02", "2023-12")
    assert np.allclose(gaps["home_energy"], 0.5)
    assert np.allclose(gaps[["food", "motor_fuel", "core"]], 0.0)


def test_pre_trend_counterfactual_recovers_2pct():
    p = synthetic_prices()
    cf = counterfactual(p, "2022-02", method="pre_trend", pre_months=24)
    assert np.allclose(cf["food"], p["food"])


def test_loss_share_is_weight_times_gap():
    p, hh = synthetic_prices(), synthetic_households()
    cf = counterfactual(p, "2022-02", method="target")
    gaps = price_gaps(p, cf, "2022-02", "2022-12")
    L = monthly_losses(gaps, hh, p, "2020")
    by_q = L.groupby(["month", "quintile"])["loss_share_spend"].sum().groupby("quintile").mean()
    assert by_q["Q1"] == pytest.approx(0.10 * 0.5)
    assert by_q["Q5"] == pytest.approx(0.04 * 0.5)


def test_euro_loss_uses_uprated_spending():
    p, hh = synthetic_prices(), synthetic_households()
    cf = counterfactual(p, "2022-02", method="target")
    gaps = price_gaps(p, cf, "2022-02", "2022-03")       # one month: 2022-03
    L = monthly_losses(gaps, hh, p, "2020")
    uprate = p.at[pd.Period("2022-03", "M"), "all_items"] / p.loc[p.index.year == 2020, "all_items"].mean()
    q1 = L[(L.quintile == "Q1") & (L.group == "home_energy")]["loss_eur"].iloc[0]
    assert q1 == pytest.approx(24000 / 12 * uprate * 0.10 * 0.5)


def test_episode_summary_and_compensation():
    p, hh = synthetic_prices(), synthetic_households()
    cfg = {
        "episodes": {"ukraine": {"label": "U", "shock_start": "2022-02", "window_end": "2023-01"}},
        "counterfactual": {"method": "target", "pre_trend_months": 24, "target_rate": 0.02, "floor_rate": 0.0},
        "cbs": {"survey_year": "2020"},
        "compensation": [
            {"name": "flat", "episode": "ukraine", "eur_per_household": [100] * 5},
            {"name": "targeted", "episode": "ukraine", "amount": 1000, "take_up_by_quintile": [0.5, 0, 0, 0, 0]},
        ],
    }
    s = run_episode(p, hh, cfg, "ukraine")["summary"]
    assert s.at["Q1", "months"] == 11
    assert s.at["Q1", "compensation_eur"] == pytest.approx(600)
    assert s.at["Q5", "compensation_eur"] == pytest.approx(100)
    assert s.at["Q1", "net_eur"] == pytest.approx(s.at["Q1", "gross_eur"] - 600)
    # regressive: lowest quintile loses a larger share of income
    assert s.at["Q1", "gross_pct_income"] > s.at["Q5", "gross_pct_income"]


def test_parse_jsonstat():
    js = {"id": ["unit", "time"], "size": [1, 2],
          "dimension": {"unit": {"category": {"index": {"I15": 0}}},
                        "time": {"category": {"index": {"2022-01": 0, "2022-02": 1}}}},
          "value": {"0": 110.0, "1": 111.5}}
    df = parse_jsonstat(js)
    assert df["value"].tolist() == [110.0, 111.5]
    assert df["time"].tolist() == ["2022-01", "2022-02"]
