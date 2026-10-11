"""How the excess price gap lands on each income quintile, in shares and euros."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import QUINTILES
from .prices import counterfactual, energy_method_correction, excess_gap

CHANNELS = ["food", "home_energy", "motor_fuel", "core"]


def spending_weights(households: pd.DataFrame, survey_year: str) -> pd.DataFrame:
    """Budget shares of cash spending, per group (Q1..Q5 and 'all').

    CBS spending includes the imputed rent of owner-occupiers. Nobody pays it,
    and HICP has no price for it, so it is taken out of the base. Leaving it in
    would understate how exposed owners are and overstate their spending.
    """
    survey = households.loc[survey_year]
    cash = 1 - survey["share_imputed_rent"]
    weights = pd.DataFrame({
        channel: survey[f"share_{channel}"] / cash for channel in ("food", "home_energy", "motor_fuel")
    })
    weights["core"] = 1 - weights.sum(axis=1)
    return weights


def cash_spending(households: pd.DataFrame, survey_year: str) -> pd.Series:
    survey = households.loc[survey_year]
    return survey["spending_eur"] * (1 - survey["share_imputed_rent"])


def monthly_income(income: pd.DataFrame, prices: pd.DataFrame, months: pd.PeriodIndex) -> pd.DataFrame:
    """Disposable income per household per month, month x quintile.

    Uses the income year of each month; after the latest CBS year, that year's
    income is uprated with the all-items index (wages roughly kept pace in
    2024–2025 [citation needed]).
    """
    annual = income["income_eur"].unstack("quintile")[QUINTILES]
    last_year = annual.index.max()
    level_last_year = prices.loc[prices.index.year == last_year, "all_items"].mean()
    income_year = months.year.to_numpy().clip(max=last_year)
    uprate = (prices["all_items"].reindex(months) / level_last_year).where(months.year > last_year, 1.0)
    base = annual.loc[income_year].set_axis(months) / 12
    return base.mul(uprate, axis=0).rename_axis("month")


def monthly_spending(spending_eur: pd.Series, prices: pd.DataFrame, survey_year: str,
                     months: pd.PeriodIndex) -> pd.DataFrame:
    """Cash spending per household per month, month x quintile, uprated from the survey year."""
    survey_prices = prices.loc[prices.index.year == int(survey_year), "all_items"]
    if survey_prices.empty:
        raise ValueError(f"price data must cover the survey year {survey_year}")
    uprate = prices["all_items"].reindex(months) / survey_prices.mean()
    return pd.DataFrame({q: uprate * spending_eur[q] / 12 for q in QUINTILES}).rename_axis("month")


def monthly_losses(gap: pd.DataFrame, weights: pd.DataFrame, spending_eur: pd.Series,
                   prices: pd.DataFrame, survey_year: str,
                   energy_correction: pd.Series | None = None) -> pd.DataFrame:
    """Long table of month x quintile x channel: loss as share of spending and in euros.

    First-order (Laspeyres) approximation: households are assumed to buy the
    same basket at higher prices. Real households cut gas use in 2022, so this
    is an upper bound on the cash loss, though not on the welfare loss.
    """
    quintile_weights = weights.loc[QUINTILES, CHANNELS]
    share = pd.concat(
        {q: gap[CHANNELS].mul(quintile_weights.loc[q]) for q in QUINTILES}, names=["quintile", "month"]
    )
    if energy_correction is not None:
        relative_exposure = weights.loc[QUINTILES, "home_energy"] / weights.at["all", "home_energy"]
        adjustment = pd.concat(
            {q: energy_correction.reindex(gap.index) * relative_exposure[q] for q in QUINTILES},
            names=["quintile", "month"],
        )
        share["home_energy"] += adjustment

    monthly_spend = monthly_spending(spending_eur, prices, survey_year, gap.index).unstack()
    long = share.stack().rename("loss_share").to_frame().rename_axis(["quintile", "month", "channel"])
    long["loss_eur"] = long["loss_share"] * monthly_spend.reindex(long.index.droplevel("channel")).to_numpy()
    return long.reset_index()


def compensation(measures: list[dict], episode: str) -> pd.DataFrame:
    rows = []
    for measure in (m for m in measures if m["episode"] == episode):
        amounts = measure.get("eur_per_household") or [
            measure["amount"] * take_up for take_up in measure["take_up_by_quintile"]
        ]
        rows += [(measure["name"], q, float(eur)) for q, eur in zip(QUINTILES, amounts)]
    return pd.DataFrame(rows, columns=["measure", "quintile", "eur"])


def summarise(losses: pd.DataFrame, comp: pd.DataFrame, income_monthly: pd.DataFrame,
              direct_channels: list[str]) -> pd.DataFrame:
    """Per quintile: euro losses, compensation and both as a share of income."""
    direct = losses[losses["channel"].isin(direct_channels)]
    summary = pd.DataFrame({
        "gross_eur": direct.groupby("quintile")["loss_eur"].sum(),
        "core_eur": losses[losses["channel"] == "core"].groupby("quintile")["loss_eur"].sum(),
        "compensation_eur": comp.groupby("quintile")["eur"].sum(),
        "income_eur": income_monthly.loc[losses["month"].unique()].sum(),
    }).reindex(QUINTILES).fillna({"compensation_eur": 0.0, "core_eur": 0.0})
    summary["net_eur"] = summary["gross_eur"] - summary["compensation_eur"]
    for column in ("gross", "net", "core"):
        summary[f"{column}_pct_income"] = summary[f"{column}_eur"] / summary["income_eur"] * 100
    summary["months"] = losses["month"].nunique()
    return summary


@dataclass
class EpisodeResult:
    gap: pd.DataFrame
    no_war: pd.DataFrame
    losses: pd.DataFrame
    compensation: pd.DataFrame
    summary: pd.DataFrame


def run_episode(cfg: dict, episode: str, prices: pd.DataFrame, households: pd.DataFrame,
                income: pd.DataFrame, research_series: pd.DataFrame | None = None,
                method: str | None = None, survey_year: str | None = None,
                energy_weight: float | None = None) -> EpisodeResult:
    spec = cfg["episodes"][episode]
    cf_spec = cfg["counterfactual"]
    survey_year = survey_year or cfg["cbs"]["survey_year"]
    energy_weight = cfg["energy_correction_weight"] if energy_weight is None else energy_weight

    columns = [c for c in [*CHANNELS, "all_items"] if c in prices]
    no_war = counterfactual(prices[columns], spec["shock_month"], method or cf_spec["method"],
                            cf_spec["target_rate"], cf_spec["pre_trend_months"])
    gap = excess_gap(prices[columns], no_war, spec["shock_month"], spec["end_month"])
    if "core" not in gap:
        gap["core"] = 0.0

    correction = None
    if energy_weight and research_series is not None:
        correction = energy_weight * energy_method_correction(research_series, gap.index, spec["shock_month"])

    weights = spending_weights(households, survey_year)
    losses = monthly_losses(gap, weights, cash_spending(households, survey_year), prices, survey_year, correction)
    comp = compensation(cfg["compensation"], episode)
    summary = summarise(losses, comp, monthly_income(income, prices, gap.index), cfg["direct_channels"])
    summary["spending_eur"] = monthly_spending(cash_spending(households, survey_year), prices, survey_year,
                                               gap.index).sum()
    summary["gross_pct_spending"] = summary["gross_eur"] / summary["spending_eur"] * 100
    return EpisodeResult(gap, no_war, losses, comp, summary)
