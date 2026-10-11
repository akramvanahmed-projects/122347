"""Static figures for the README and report. Saved to figures/ as PNG (300 dpi) and SVG.

One strong colour (war red) carries the finding in every chart; everything
else is grey. Titles state the result, subtitles say exactly what is plotted.
"""
from __future__ import annotations

import json

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Circle, Rectangle

from .analysis import load_inputs, run_all
from .config import FIGURES, QUINTILES, ROOT
from .exposure import EpisodeResult
from .health import totals

RED = "#a50f15"
RED_LIGHT = "#f4c6c3"
INK = "#1f1f1f"
GREY_DARK = "#555555"
GREY = "#9a9a9a"
GREY_LIGHT = "#dcdcdc"
QUINTILE_NAMES = ["Poorest\nfifth", "Second", "Middle", "Fourth", "Richest\nfifth"]


def _apply_style() -> None:
    family = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
    mpl.rcParams.update({
        "font.family": family,
        "font.size": 10,
        "axes.edgecolor": GREY,
        "axes.labelcolor": GREY_DARK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": False,
        "xtick.color": GREY_DARK,
        "ytick.color": GREY_DARK,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.fonttype": "none",
    })


def _titles(fig: plt.Figure, title: str, subtitle: str, source: str) -> None:
    title_artist = fig.text(0.02, 0.975, title, fontsize=14, fontweight="bold", color=INK, va="top",
                            linespacing=1.25)
    fig.canvas.draw()
    title_bottom = fig.transFigure.inverted().transform(
        title_artist.get_window_extent().get_points())[0][1]
    fig.text(0.02, title_bottom - 0.025, subtitle, fontsize=9.5, color=GREY_DARK, va="top", linespacing=1.4)
    fig.text(0.02, 0.015, source, fontsize=7.5, color=GREY, va="bottom", linespacing=1.4)


def _save(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(exist_ok=True)
    for suffix, kwargs in ((".png", {"dpi": 300}), (".svg", {})):
        fig.savefig(FIGURES / f"{name}{suffix}", **kwargs)
    plt.close(fig)


def _months_since_shock(result: EpisodeResult) -> np.ndarray:
    return np.arange(1, len(result.gap) + 1)


def _mean_household_share(result: EpisodeResult, channels: list[str]) -> pd.DataFrame:
    """Excess cost as % of monthly spending for the mean of the five quintiles, month x channel."""
    losses = result.losses[result.losses["channel"].isin(channels)]
    return losses.groupby(["month", "channel"])["loss_share"].mean().unstack()[channels] * 100


# Figure 1 ----------------------------------------------------------------------

def _month_name(period: str) -> str:
    return pd.Period(period, "M").strftime("%B %Y")


def bleeding_income(result: EpisodeResult, numbers: dict) -> None:
    """Losses hang below the income line like a wound; the grey part is what support closed."""
    summary = result.summary
    gross = summary["gross_pct_income"].to_numpy()
    net = summary["net_pct_income"].to_numpy()
    x = np.arange(len(QUINTILES))
    width = 0.56

    fig, ax = plt.subplots(figsize=(8, 6))
    fig.subplots_adjust(left=0.1, right=0.95, top=0.66, bottom=0.12)
    ax.axhline(0, color=INK, lw=1.4, zorder=3)

    for xi, g, n in zip(x, gross, net):
        ax.add_patch(Rectangle((xi - width / 2, -g), width, g, facecolor=GREY_LIGHT, edgecolor="none", zorder=1))
        ax.text(xi + width / 2 + 0.03, -g, f"{g:.1f}%", ha="left", va="center", fontsize=8.5, color=GREY)
        if n > 0:
            ax.add_patch(Rectangle((xi - width / 2, -n), width, n, facecolor=RED, edgecolor="none", zorder=2))
            ax.text(xi, -n / 2, f"{n:.1f}%", ha="center", va="center", fontsize=11, fontweight="bold",
                    color="white", zorder=4)
        else:
            ax.add_patch(Rectangle((xi - width / 2, 0), width, -n, facecolor=GREY_DARK, edgecolor="none", zorder=2))
            ax.text(xi, -n + 0.1, f"{-n:.1f}% ahead*", ha="center", va="bottom", fontsize=10,
                    fontweight="bold", color=GREY_DARK)

    ax.text(x[0] + width / 2 + 0.03, -gross[0] - 0.28, "before support", fontsize=8.5, color=GREY, va="center")
    ax.text(x[1] - width / 2 - 0.04, -net[1] / 2, "after\nsupport", fontsize=8.5, color=RED, va="center", ha="right")
    ax.text(-0.82, 0.12, "gained", fontsize=8, color=GREY_DARK, va="bottom")
    ax.text(-0.82, -0.12, "lost", fontsize=8, color=RED, va="top")

    ax.set_xlim(-0.85, len(QUINTILES) - 0.35)
    ax.set_ylim(-np.ceil(max(gross)) - 0.3, max(-net.min(), 0) + 0.7)
    ax.set_xticks(x, QUINTILE_NAMES)
    ax.xaxis.set_ticks_position("top")
    ax.tick_params(axis="x", pad=6, labelsize=9.5)
    ticks = np.arange(-np.ceil(max(gross)), 0, 1)
    ax.set_yticks(ticks, [f"{abs(t):.0f}%" for t in ticks], fontsize=8.5)
    ax.spines["bottom"].set_visible(False)

    _titles(
        fig,
        "Support erased the poorest fifth's war loss.\nEveryone else still paid.",
        "Excess spending on food, home energy and motor fuel during the Russia–Ukraine price shock,\n"
        f"{_month_name(numbers['first_month'])} to {_month_name(numbers['last_month'])}, as a share of each "
        "income fifth's disposable income.",
        "* Assumes 55% of the poorest fifth claimed the €1,300 energietoeslag in both years; break-even is "
        f"{numbers['q1_break_even_take_up']:.0%}.\n"
        "Source: Eurostat HICP (prc_hicp_minr); CBS 85420NED, 85419NED, 83932NED. Midpoint CBS energy-method correction.",
    )
    _save(fig, "01_bleeding_income")


# Figure 2 ----------------------------------------------------------------------

def wave_and_ripple(results: dict[str, EpisodeResult], channels: list[str]) -> None:
    ukraine = _mean_household_share(results["ukraine"], channels).sum(axis=1)
    iran = _mean_household_share(results["iran"], channels).sum(axis=1)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    fig.subplots_adjust(left=0.08, right=0.95, top=0.74, bottom=0.16)
    xu, xi = np.arange(1, len(ukraine) + 1), np.arange(1, len(iran) + 1)
    ax.fill_between(xu, 0, ukraine, color=GREY_LIGHT, lw=0, step="mid")
    ax.plot(xu, ukraine, color=GREY, lw=1.2, drawstyle="steps-mid")
    ax.fill_between(xi, 0, iran, color=RED, lw=0, step="mid", alpha=0.9)
    ax.axhline(0, color=INK, lw=1)

    peak = ukraine.idxmax()
    peak_x = list(ukraine.index).index(peak) + 1
    ax.annotate(f"Ukraine: peak {ukraine.max():.1f}% of spending\n({peak.strftime('%b %Y')})",
                xy=(peak_x, ukraine.max()), xytext=(peak_x + 2.5, ukraine.max() - 0.3),
                fontsize=9, color=GREY_DARK, arrowprops={"arrowstyle": "-", "color": GREY, "lw": 0.8})
    ax.annotate(f"Iran, so far: {iran.iloc[-1]:.1f}%\n({iran.index[-1].strftime('%b %Y')})",
                xy=(len(iran), iran.iloc[-1]), xytext=(len(iran) + 1.5, 1.4),
                fontsize=9.5, color=RED, fontweight="bold",
                arrowprops={"arrowstyle": "-", "color": RED, "lw": 0.9})

    ax.set_xlim(0.5, len(ukraine) + 0.5)
    ax.set_ylim(0, ukraine.max() * 1.18)
    ax.set_xticks([1, 6, 12, 18, len(ukraine)], ["1", "6", "12", "18", str(len(ukraine))], fontsize=8.5)
    ax.set_xlabel("months after the war began", fontsize=9)
    ax.set_yticks([0, 1, 2, 3, 4, 5], ["0", "1%", "2%", "3%", "4%", "5%"], fontsize=8.5)
    ax.yaxis.grid(True, color=GREY_LIGHT, lw=0.6)
    ax.set_axisbelow(True)
    _titles(
        fig,
        "Six months in, the Iran shock is a ripple next to Ukraine's wave",
        "Excess monthly cost of food, home energy and motor fuel for the average household,\n"
        "as a share of its monthly spending, aligned on the month each war began.",
        "Source: Eurostat HICP (prc_hicp_minr), CBS Budgetonderzoek 2020. Counterfactual: shock-month prices growing 2% a year.",
    )
    _save(fig, "02_wave_and_ripple")


# Figure 3 ----------------------------------------------------------------------

def the_gap_is_the_bill(results: dict[str, EpisodeResult], prices: pd.DataFrame, cfg: dict) -> None:
    panels = [("ukraine", "home_energy", "Home energy, Ukraine"),
              ("ukraine", "food", "Food, Ukraine"),
              ("iran", "motor_fuel", "Motor fuel, Iran")]
    fig, axes = plt.subplots(1, 3, figsize=(10, 4.4), sharey=False)
    fig.subplots_adjust(left=0.05, right=0.98, top=0.7, bottom=0.14, wspace=0.28)
    for ax, (episode, channel, label) in zip(axes, panels):
        result = results[episode]
        shock = pd.Period(cfg["episodes"][episode]["shock_month"], "M")
        window = slice(shock - 6, result.gap.index.max())
        base = prices.at[shock, channel]
        actual = prices.loc[window, channel] / base * 100
        no_war = result.no_war.loc[window, channel] / base * 100
        t = actual.index.to_timestamp()
        ax.fill_between(t, no_war, actual, where=actual >= no_war, color=RED, alpha=0.85, lw=0, interpolate=True)
        ax.fill_between(t, no_war, actual, where=actual < no_war, color=GREY_LIGHT, lw=0, interpolate=True)
        ax.plot(t, no_war, color=GREY_DARK, lw=1, ls=(0, (3, 2)))
        ax.plot(t, actual, color=INK, lw=1.3)
        ax.axvline(shock.to_timestamp(), color=GREY, lw=0.8)
        ax.set_title(label, loc="left", fontsize=10, fontweight="bold", color=INK)
        ax.text(t[-1], no_war.iloc[-1], "no war ", fontsize=8, color=GREY_DARK, ha="right",
                va="top" if actual.iloc[-1] > no_war.iloc[-1] else "bottom")
        ax.yaxis.grid(True, color=GREY_LIGHT, lw=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=8)
        ax.xaxis.set_major_locator(mpl.dates.MonthLocator(bymonth=[1, 7]))
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b\n%Y"))
    axes[0].set_ylabel("price index, war month = 100", fontsize=8.5)
    _titles(
        fig,
        "Energy spiked and fell back. Food never came down.",
        "Actual consumer prices (solid) against a no-war path that grows 2% a year from the month each war began (dashed).\n"
        "Red is what households paid above that path.",
        "Source: Eurostat HICP (prc_hicp_minr), Netherlands, 2015=100 rebased. Published energy series, before the CBS method correction.",
    )
    _save(fig, "03_the_gap_is_the_bill")


# Figure 4 ----------------------------------------------------------------------

def what_drove_it(result: EpisodeResult) -> None:
    shares = _mean_household_share(result, ["food", "home_energy", "motor_fuel"])
    t = shares.index.to_timestamp()
    colors = {"food": RED, "home_energy": GREY_DARK, "motor_fuel": GREY_LIGHT}
    labels = {"food": "Food", "home_energy": "Home energy", "motor_fuel": "Motor fuel"}

    fig, ax = plt.subplots(figsize=(8, 4.8))
    fig.subplots_adjust(left=0.08, right=0.84, top=0.74, bottom=0.12)
    positive, negative = shares.clip(lower=0), shares.clip(upper=0)
    bottom_pos = np.zeros(len(shares))
    bottom_neg = np.zeros(len(shares))
    for channel in ["home_energy", "food", "motor_fuel"]:
        ax.bar(t, positive[channel], bottom=bottom_pos, width=25, color=colors[channel], lw=0)
        ax.bar(t, negative[channel], bottom=bottom_neg, width=25, color=colors[channel], lw=0)
        bottom_pos += positive[channel].to_numpy()
        bottom_neg += negative[channel].to_numpy()
    ax.axhline(0, color=INK, lw=1)

    last = shares.iloc[-1]
    stack = {"home_energy": max(last["home_energy"], 0) / 2,
             "food": max(last["home_energy"], 0) + max(last["food"], 0) / 2,
             "motor_fuel": min(last["motor_fuel"], 0) / 2 - 0.15}
    for channel, y in stack.items():
        ax.text(t[-1] + pd.Timedelta(days=22), y, labels[channel], va="center", fontsize=9,
                color=RED if channel == "food" else GREY_DARK, fontweight="bold" if channel == "food" else "normal")

    ax.yaxis.grid(True, color=GREY_LIGHT, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_yticks(range(-1, 6), [f"{v}%" if v else "0" for v in range(-1, 6)], fontsize=8.5)
    ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b\n%Y"))
    ax.tick_params(axis="x", labelsize=8.5)
    _titles(
        fig,
        "Energy hit first. From January 2023, food carried the war bill.",
        "Excess monthly cost by category for the average household, Russia–Ukraine shock,\n"
        "as a share of monthly spending. Below zero: prices fell under the no-war path (fuel excise cut, price ceiling).",
        "Source: Eurostat HICP (prc_hicp_minr), CBS Budgetonderzoek 2020. Midpoint CBS energy-method correction.",
    )
    _save(fig, "04_what_drove_it")


# Figure 5 ----------------------------------------------------------------------

def lifetimes(lives: dict[str, pd.DataFrame], cfg: dict) -> None:
    """One dot per 82-year lifetime. Red: lost after support. Grey ring: prevented by support."""
    life_expectancy = cfg["human_cost"]["life_expectancy"]
    fig = plt.figure(figsize=(9, 6.6))
    _titles(
        fig,
        "The Ukraine shock cost the Netherlands about 110 lifetimes.\nSupport prevented 70 more.",
        f"Each dot is one full {life_expectancy:.0f}-year life: life-years lost to lower income, summed over 18 million people\n"
        "and divided by life expectancy. An equivalence, not a death count.",
        "Method: CBS income–longevity gradient (8.5 years between richest and poorest fifth), 25% assumed causal\n"
        "(range 10–50%), scaled to the length of the shock. Central estimate after support.",
    )
    columns, width_frac, fig_w, fig_h = 25, 0.66, 9, 6.6
    row_frac = width_frac * fig_w / columns / fig_h       # one dot cell, same size in both panels
    for row, (episode, label) in enumerate([("ukraine", "Russia–Ukraine war"), ("iran", "Iran war, to date")]):
        t = totals(lives[episode])
        net = int(round(t.at[("central", "net"), "lifetimes"]))
        prevented = int(round(t.at[("central", "gross"), "lifetimes"])) - net
        low, high = t.at[("low", "net"), "lifetimes"], t.at[("high", "net"), "lifetimes"]
        top = 0.74 if row == 0 else 0.33
        n_dots = net + prevented
        rows_needed = max(1, int(np.ceil(n_dots / columns)))
        ax = fig.add_axes([0.3, top - rows_needed * row_frac, width_frac, rows_needed * row_frac])
        for i in range(n_dots):
            cx, cy = i % columns, -(i // columns)
            if i < net:
                ax.add_patch(Circle((cx, cy), 0.36, facecolor=RED, edgecolor="none"))
            else:
                ax.add_patch(Circle((cx, cy), 0.33, facecolor="none", edgecolor=GREY, lw=1.0))
        ax.set_xlim(-0.5, columns - 0.5)
        ax.set_ylim(-rows_needed + 0.5, 0.5)
        ax.axis("off")
        fig.text(0.04, top, label, fontsize=11, fontweight="bold", color=INK, va="top")
        fig.text(0.04, top - 0.04, f"{net} lifetimes lost", fontsize=17, fontweight="bold", color=RED, va="top")
        detail = f"range {low:.0f}–{high:.0f}"
        if prevented:
            detail += f"\n{prevented} more prevented by\nsupport (open dots)"
        fig.text(0.04, top - 0.1, detail, fontsize=9, color=GREY_DARK, va="top", linespacing=1.4)
    _save(fig, "05_lifetimes")


# Figure 6 ----------------------------------------------------------------------

def support_while_it_lasted(cfg: dict, ukraine: EpisodeResult, break_even: float) -> None:
    indicators = cfg["indicators"]
    poverty = pd.Series(indicators["energy_poverty_pct"], dtype=float)
    kept_out = pd.Series(indicators["kept_out_by_support_pct"], dtype=float).reindex(poverty.index).fillna(0)
    years = poverty.index.astype(int)

    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw={"width_ratios": [1.25, 1]})
    fig.subplots_adjust(left=0.06, right=0.97, top=0.7, bottom=0.14, wspace=0.3)

    left.axvspan(2021.5, 2023.5, color="#f7f7f7", lw=0)
    left.text(2022.5, 10.6, "support paid", ha="center", fontsize=8.5, color=GREY_DARK)
    left.bar(years, poverty, color=[RED if y >= 2024 else GREY for y in years], width=0.62, lw=0)
    left.bar(years, kept_out, bottom=poverty, color="white", edgecolor=GREY, hatch="////", width=0.62, lw=0.8)
    for y, p in zip(years, poverty):
        left.text(y, p / 2, f"{p:.1f}", ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
    left.text(2023, poverty["2023"] + kept_out["2023"] + 0.3, "would have been\nwithout support",
              ha="center", fontsize=8, color=GREY_DARK)
    left.set_ylim(0, 11.5)
    left.set_yticks([0, 5, 10], ["0", "5%", "10%"], fontsize=8.5)
    left.set_xticks(years, [str(y) for y in years], fontsize=8.5)
    left.set_title("Households in energy poverty", loc="left", fontsize=10, fontweight="bold", color=INK)

    gross = ukraine.summary.at["Q1", "gross_eur"]
    flat = sum(m["eur_per_household"][0] for m in cfg["compensation"]
               if m["episode"] == "ukraine" and "eur_per_household" in m)
    targeted = sum(m["amount"] for m in cfg["compensation"] if m["episode"] == "ukraine" and "amount" in m)
    take_up = np.linspace(0, 1, 101)
    net = gross - flat - targeted * take_up
    right.axhline(0, color=INK, lw=1)
    right.plot(take_up * 100, net, color=GREY_DARK, lw=1.6)
    right.fill_between(take_up * 100, net, 0, where=net > 0, color=RED, alpha=0.85, lw=0)
    right.fill_between(take_up * 100, net, 0, where=net <= 0, color=GREY_LIGHT, lw=0)
    right.axvline(break_even * 100, color=RED, lw=0.9, ls=(0, (3, 2)))
    right.text(break_even * 100 + 2, gross - flat - 80, f"break-even at\n{break_even:.0%} take-up",
               fontsize=9, color=RED, fontweight="bold", va="top")
    right.text(62, -330, "came out ahead", fontsize=8.5, color=GREY_DARK)
    right.text(12, 640, "still lost", fontsize=8.5, color=RED)
    right.set_xlabel("share of the poorest fifth claiming the energietoeslag", fontsize=8.5)
    right.set_yticks([-1500, -1000, -500, 0, 500, 1000], ["−€1,500", "−€1,000", "−€500", "0", "€500", "€1,000"],
                     fontsize=8.5)
    right.set_xticks([0, 25, 50, 75, 100], ["0", "25%", "50%", "75%", "100%"], fontsize=8.5)
    right.yaxis.grid(True, color=GREY_LIGHT, lw=0.6)
    right.set_axisbelow(True)
    right.set_title("Poorest fifth: net war cost per household", loc="left", fontsize=10, fontweight="bold",
                    color=INK)

    _titles(
        fig,
        "Support worked while it lasted",
        "Energy poverty fell during the Ukraine shock because support kept households out (hatched),\n"
        "then rose to 6% once payments ended. For the poorest fifth, the result turns on who claimed.",
        "Source: CBS/TNO energy poverty monitor (2023–2025 preliminary); model results. Energietoeslag €1,300 in 2022 and 2023, "
        "plus €380 for every household.",
    )
    _save(fig, "06_support_while_it_lasted")


def draw_all(cfg: dict) -> None:
    _apply_style()
    inputs = load_inputs(cfg)
    results = run_all(cfg, inputs)
    numbers = json.loads((ROOT / "reports" / "key_numbers.json").read_text())
    lives = {episode: pd.read_csv(ROOT / "data" / "processed" / f"human_cost_{episode}.csv")
             for episode in results}
    bleeding_income(results["ukraine"], numbers["ukraine"])
    wave_and_ripple(results, cfg["direct_channels"])
    the_gap_is_the_bill(results, inputs["prices"], cfg)
    what_drove_it(results["ukraine"])
    lifetimes(lives, cfg)
    support_while_it_lasted(cfg, results["ukraine"], numbers["ukraine"]["q1_break_even_take_up"])
