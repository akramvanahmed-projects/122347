"""Download Eurostat and CBS tables and reduce them to tidy, model-ready files.

Raw downloads are cached in data/raw (not committed). Outputs in
data/processed: prices.csv, households.csv, income.csv.
"""
from __future__ import annotations

import itertools
import logging

import pandas as pd
import requests

from .config import PROCESSED, QUINTILES, RAW

log = logging.getLogger(__name__)
EUROSTAT_API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}"


# Eurostat ---------------------------------------------------------------------

def parse_jsonstat(payload: dict) -> pd.DataFrame:
    """Flatten a Eurostat JSON-stat 2.0 response into one row per observation."""
    dims = payload["id"]
    categories = []
    for dim in dims:
        index = payload["dimension"][dim]["category"]["index"]
        categories.append(sorted(index, key=index.get))
    values = payload["value"]
    rows = [
        (*combo, values[str(position)])
        for position, combo in enumerate(itertools.product(*categories))
        if str(position) in values
    ]
    return pd.DataFrame(rows, columns=[*dims, "value"])


def fetch_hicp_series(dataset: str, geo: str, unit: str, code: str, start: str) -> pd.Series:
    # ECOICOP 2 datasets name the classification dimension "coicop18".
    for dim in ("coicop18", "coicop"):
        response = requests.get(
            EUROSTAT_API.format(dataset=dataset),
            params={"geo": geo, "unit": unit, dim: code, "sinceTimePeriod": start},
            timeout=60,
        )
        if response.ok:
            observations = parse_jsonstat(response.json())
            if not observations.empty:
                break
    else:
        raise LookupError(f"{dataset}: no {unit} series for {code} in {geo}; "
                          f"available: {available_codes(dataset, geo)}")
    series = observations.set_index("time")["value"].astype(float)
    series.index = pd.PeriodIndex(series.index, freq="M")
    return series.sort_index()


def available_codes(dataset: str, geo: str) -> str:
    response = requests.get(EUROSTAT_API.format(dataset=dataset),
                            params={"geo": geo, "sinceTimePeriod": "2026-01", "untilTimePeriod": "2026-01"},
                            timeout=120)
    if not response.ok:
        return f"HTTP {response.status_code}"
    observations = parse_jsonstat(response.json())
    dim = "coicop18" if "coicop18" in observations else "coicop"
    units = sorted(observations["unit"].unique())
    return f"units={units} codes={' '.join(sorted(observations[dim].unique()))}"


def build_prices(cfg: dict) -> pd.DataFrame:
    spec = cfg["prices"]
    columns = {}
    for category, code in spec["coicop"].items():
        try:
            columns[category] = fetch_hicp_series(spec["dataset"], spec["geo"], spec["unit"], code, spec["start"])
        except LookupError:
            if category != "core":
                raise
            log.warning("core index %s unavailable; core sensitivity disabled", code)
    prices = pd.DataFrame(columns).dropna()
    prices.index.name = "month"
    return prices


# CBS -------------------------------------------------------------------------

def cbs_table(table: str) -> pd.DataFrame:
    """Full CBS StatLine table, cached as CSV in data/raw."""
    cache = RAW / f"{table}.csv"
    if cache.exists():
        return pd.read_csv(cache, dtype={"Perioden": str})
    import cbsodata

    frame = pd.DataFrame(cbsodata.get_data(table))
    frame["Perioden"] = frame["Perioden"].astype(str).str.strip()
    RAW.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cache, index=False)
    return frame


def _value_column(frame: pd.DataFrame) -> str:
    numeric = [c for c in frame.select_dtypes("number").columns if c != "ID"]
    return numeric[0]


def household_groups(cfg: dict) -> dict[str, str]:
    """CBS label -> our group name, for the five quintiles and all households."""
    labels = {cfg["cbs"]["quintile_label"].format(n=n): q for n, q in enumerate(QUINTILES, start=1)}
    labels[cfg["cbs"]["all_households_label"]] = "all"
    return labels


def build_households(cfg: dict) -> pd.DataFrame:
    """Spending shares and total spending per income quintile, for each survey year.

    Rows are matched on the COICOP code that starts every CBS category label,
    which is stable across table revisions in a way the Dutch wording is not.
    """
    groups = household_groups(cfg)
    code_to_name = {code: name for name, code in cfg["cbs"]["categories"].items()}

    shares = cbs_table(cfg["cbs"]["shares_table"])
    shares = shares.assign(
        code=shares["Bestedingscategorieen"].str.split().str[0],
        group=shares["KenmerkenHuishoudens"].map(groups),
    ).query("group.notna() and code in @code_to_name")
    share_wide = (
        shares.assign(category=shares["code"].map(code_to_name), share=shares[_value_column(shares)] / 100)
        .pivot_table(index=["Perioden", "group"], columns="category", values="share")
        .drop(columns="total")
        .add_prefix("share_")
    )

    spending = cbs_table(cfg["cbs"]["spending_table"])
    spending = spending[
        spending["Bestedingscategorieen"].str.startswith(cfg["cbs"]["categories"]["total"])
        & spending["KenmerkenHuishoudens"].isin(groups)
    ]
    total = (
        spending.assign(group=spending["KenmerkenHuishoudens"].map(groups),
                        spending_eur=spending[_value_column(spending)] * 1000)
        .set_index(["Perioden", "group"])["spending_eur"]
    )

    households = share_wide.join(total, how="inner")
    households.index.names = ["survey_year", "group"]
    missing = {(y, g) for y in households.index.levels[0] for g in [*QUINTILES, "all"]} - set(households.index)
    if missing:
        raise ValueError(f"CBS household rows missing: {sorted(missing)}")
    return households.sort_index()


def build_income(cfg: dict) -> pd.DataFrame:
    """Mean disposable income, households and persons per quintile and year.

    CBS publishes deciles; quintiles are household-weighted pairs of deciles.
    The standardised-income column (equivalised for household size) is what the
    CBS life-expectancy studies rank people by, so it is kept for the gradient.
    """
    income = cbs_table(cfg["cbs"]["income_table"])
    income = income[income["KenmerkenVanHuishoudens"] == cfg["cbs"]["all_households_label"]]
    decile_label = cfg["cbs"]["income_decile_label"]
    decile_of = {}
    for n in range(1, 11):
        decile_of[decile_label.format(n=n)] = n
    income = income.assign(
        decile=income["Inkomensklassen"].str.replace(r"\s*\(.*\)$", "", regex=True).map(decile_of)
    ).dropna(subset=["decile"])
    income["quintile"] = "Q" + ((income["decile"] + 1) // 2).astype(int).astype(str)
    income["households"] = income["ParticuliereHuishoudens_1"] * 1000
    income["mean_eur"] = income["GemiddeldInkomen_4"] * 1000

    def by_concept(concept: str, value_name: str) -> pd.Series:
        subset = income[income["Inkomensbegrippen"] == concept]
        weighted = subset.assign(total=subset["mean_eur"] * subset["households"])
        grouped = weighted.groupby(["Perioden", "quintile"])
        return (grouped["total"].sum() / grouped["households"].sum()).rename(value_name)

    disposable = income[income["Inkomensbegrippen"] == cfg["cbs"]["income_concept"]]
    counts = disposable.assign(persons=disposable["households"] * disposable["PersonenPerHuishouden_2"])
    counts = counts.groupby(["Perioden", "quintile"])[["households", "persons"]].sum()

    table = pd.concat(
        [by_concept(cfg["cbs"]["income_concept"], "income_eur"),
         by_concept("Gestandaardiseerd inkomen", "standardised_income_eur"),
         counts],
        axis=1,
    )
    table.index.names = ["year", "quintile"]
    return table.dropna(subset=["income_eur"]).sort_index()


def build_all(cfg: dict) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    build_prices(cfg).to_csv(PROCESSED / "prices.csv")
    build_households(cfg).to_csv(PROCESSED / "households.csv")
    build_income(cfg).to_csv(PROCESSED / "income.csv")


def load_processed() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prices = pd.read_csv(PROCESSED / "prices.csv", index_col="month")
    prices.index = pd.PeriodIndex(prices.index, freq="M")
    households = pd.read_csv(PROCESSED / "households.csv", index_col=["survey_year", "group"],
                             dtype={"survey_year": str})
    income = pd.read_csv(PROCESSED / "income.csv", index_col=["year", "quintile"])
    return prices, households, income
