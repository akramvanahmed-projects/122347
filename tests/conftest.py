"""Synthetic inputs with known answers. None of these numbers are real data."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from warcost.config import QUINTILES, ROOT, load_config

MONTHS = pd.period_range("2014-01", "2026-09", freq="M")
GROUPS = [*QUINTILES, "all"]


@pytest.fixture
def cfg() -> dict:
    return load_config(ROOT / "config.yaml")


@pytest.fixture
def prices() -> pd.DataFrame:
    """Every index grows 2% a year; home energy jumps 50% after Feb 2022 and again after Feb 2026."""
    level = 100 * 1.02 ** (np.arange(len(MONTHS)) / 12)
    frame = pd.DataFrame({c: level for c in ["food", "home_energy", "motor_fuel", "core", "all_items"]},
                         index=MONTHS)
    frame.loc[MONTHS > pd.Period("2022-02", "M"), "home_energy"] *= 1.5
    frame.loc[MONTHS > pd.Period("2026-02", "M"), "home_energy"] *= 1.2
    frame.index.name = "month"
    return frame


@pytest.fixture
def households() -> pd.DataFrame:
    shares = {
        "share_food": [0.15, 0.14, 0.13, 0.12, 0.10, 0.13],
        "share_home_energy": [0.08, 0.07, 0.06, 0.05, 0.04, 0.06],
        "share_motor_fuel": [0.02, 0.03, 0.04, 0.04, 0.04, 0.035],
        "share_imputed_rent": [0.0, 0.05, 0.10, 0.15, 0.20, 0.10],
        "spending_eur": [24000, 30000, 36000, 42000, 54000, 37200],
    }
    frames = {year: pd.DataFrame(shares, index=pd.Index(GROUPS, name="group")) for year in ("2015", "2020")}
    return pd.concat(frames, names=["survey_year", "group"])


@pytest.fixture
def income() -> pd.DataFrame:
    years = range(2018, 2025)
    rows = []
    for year in years:
        for q, (eur, std) in zip(QUINTILES, [(20000, 15000), (32000, 24000), (45000, 32000),
                                             (62000, 42000), (100000, 67500)]):
            rows.append((year, q, eur, std, 1_600_000, 3_360_000))
    return pd.DataFrame(rows, columns=["year", "quintile", "income_eur", "standardised_income_eur",
                                       "households", "persons"]).set_index(["year", "quintile"])
