"""Parsing tests against miniature tables that copy the real CBS label formats."""
import pandas as pd
import pytest

from warcost import sources
from warcost.sources import build_households, build_income, parse_jsonstat

QUINTILE_LABELS = [f"Besteedbaar inkomen: {n}e 20%-groep" for n in range(1, 6)]
GROUP_LABELS = ["Particuliere huishoudens", *QUINTILE_LABELS, "Type: Eenpersoonshuishouden"]
CATEGORIES = {"000000 Alle bestedingen": 100.0, "010000 Voedingsmidd. en alc.vrije drank": 12.0,
              "011000 Voedingsmiddelen": 10.0, "042000 Toegerekende huur eigen woning": 10.0,
              "045000 Energie": 5.0, "045100 Elektriciteit": 2.0, "072200 Brandstoffen en smeermiddelen": 4.0}


def shares_table() -> pd.DataFrame:
    rows = [(cat, grp, year, value) for cat, value in CATEGORIES.items() for grp in GROUP_LABELS
            for year in ("2015", "2020")]
    return pd.DataFrame(rows, columns=["Bestedingscategorieen", "KenmerkenHuishoudens", "Perioden",
                                       "Bestedingsaandeel_1"])


def spending_table() -> pd.DataFrame:
    rows = [(cat, grp, year, 35.2) for cat in ("000000 Alle bestedingen", "010000 Voedingsmidd. en alc.vrije drank")
            for grp in GROUP_LABELS for year in ("2015", "2020")]
    return pd.DataFrame(rows, columns=["Bestedingscategorieen", "KenmerkenHuishoudens", "Perioden",
                                       "GemiddeldBesteedBedrag_1"])


def income_table() -> pd.DataFrame:
    labels = ["Inkomen: 1e 10%-groep (laag inkomen)"] + [f"Inkomen: {n}e 10%-groep" for n in range(2, 10)] \
        + ["Inkomen: 10e 10%-groep (hoog inkomen)", "Totaal"]
    rows = []
    for concept in ("Besteedbaar inkomen", "Gestandaardiseerd inkomen", "Primair inkomen"):
        for n, label in enumerate(labels, start=1):
            rows.append((concept, label, "Particuliere huishoudens", "2024", 800.0 + n, 2.0, 10.0 * n, 9.0 * n))
    return pd.DataFrame(rows, columns=["Inkomensbegrippen", "Inkomensklassen", "KenmerkenVanHuishoudens",
                                       "Perioden", "ParticuliereHuishoudens_1", "PersonenPerHuishouden_2",
                                       "GemiddeldInkomen_4", "MediaanInkomen_5"])


@pytest.fixture
def fake_cbs(monkeypatch, cfg):
    tables = {cfg["cbs"]["shares_table"]: shares_table(), cfg["cbs"]["spending_table"]: spending_table(),
              cfg["cbs"]["income_table"]: income_table()}
    monkeypatch.setattr(sources, "cbs_table", tables.__getitem__)


def test_households_matched_on_coicop_codes(fake_cbs, cfg):
    households = build_households(cfg)
    q1 = households.loc[("2020", "Q1")]
    assert q1["share_food"] == pytest.approx(0.12)          # 010000, not the 011000 sub-row
    assert q1["share_home_energy"] == pytest.approx(0.05)
    assert q1["share_imputed_rent"] == pytest.approx(0.10)
    assert q1["spending_eur"] == pytest.approx(35200)
    assert set(households.index.get_level_values("group")) == {"Q1", "Q2", "Q3", "Q4", "Q5", "all"}


def test_income_quintiles_pair_deciles(fake_cbs, cfg):
    income = build_income(cfg)
    q1 = income.loc[(2024, "Q1")] if 2024 in income.index.get_level_values(0) else income.loc[("2024", "Q1")]
    # deciles 1 and 2: means 10k and 20k with 801k and 802k households
    assert q1["income_eur"] == pytest.approx((10_000 * 801 + 20_000 * 802) / 1603)
    assert q1["households"] == pytest.approx(1_603_000)
    assert q1["persons"] == pytest.approx(3_206_000)


def test_parse_jsonstat():
    payload = {"id": ["unit", "time"], "size": [1, 2],
               "dimension": {"unit": {"category": {"index": {"I15": 0}}},
                             "time": {"category": {"index": {"2022-01": 0, "2022-02": 1}}}},
               "value": {"0": 110.0, "1": 111.5}}
    frame = parse_jsonstat(payload)
    assert frame["value"].tolist() == [110.0, 111.5]
