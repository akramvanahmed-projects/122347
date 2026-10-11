"""Streamlit app: the data story as the front page, the model explorer as the second.

    streamlit run app.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

# Streamlit Cloud installs requirements.txt (which includes the package), but the
# app should also run straight from a fresh clone.
sys.path.insert(0, str(Path(__file__).parent / "src"))

import plotly.graph_objects as go
import streamlit as st

from warcost.analysis import human_cost, load_inputs, run_all
from warcost.config import QUINTILES, ROOT, load_config
from warcost.health import totals

RED, GREY_LIGHT, GREY_DARK, INK = "#dc1c13", "#d9dadd", "#5a5d63", "#111214"
QUINTILE_NAMES = ["Poorest fifth", "Second", "Middle", "Fourth", "Richest fifth"]
DISCLAIMER = ("Independent analysis, not affiliated with CBS, Eurostat or any government body. Model estimates, "
              "not official statistics, and not medical, financial or legal advice. Provided as is, without "
              "warranty. Made with the assistance of Claude (Anthropic).")

st.set_page_config(page_title="Hidden casualties", layout="wide", initial_sidebar_state="collapsed")


def story() -> None:
    """The story page, built by `python -m warcost story`, shown full height."""
    page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    html = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>"
            f"</head><body>{page}</body></html>")
    st.markdown(
        "<style>.block-container{padding:0.5rem 0 0 0 !important;max-width:100% !important}"
        "iframe{border:0}</style>",
        unsafe_allow_html=True,
    )
    # Our own built page, not user input, so embedding it unsanitised is safe.
    st.iframe(html, height="content")


@st.cache_data
def base_inputs() -> tuple[dict, dict]:
    return load_config(), load_inputs(load_config())


def styled(fig: go.Figure, y_title: str) -> go.Figure:
    fig.update_layout(height=380, margin={"l": 10, "r": 10, "t": 30, "b": 10}, plot_bgcolor="#fbfbf9",
                      paper_bgcolor="#fbfbf9", showlegend=False, yaxis_title=y_title,
                      font={"size": 13, "color": INK, "family": "Helvetica Neue, Arial, sans-serif"})
    fig.update_yaxes(gridcolor="#e6e6e3", zerolinecolor=INK)
    return fig


def net_label(pct: float) -> str:
    return f"{pct:.1f}% lost" if pct >= 0 else f"{-pct:.1f}% ahead"


def explorer() -> None:
    base_cfg, inputs = base_inputs()

    st.title("Model explorer")
    st.caption("Change the contested choices and watch the numbers move. "
               f"Prices to {inputs['prices'].index.max()}.")

    controls, view = st.columns([1, 3], gap="large")
    with controls:
        st.subheader("Contested choices")
        energy_weight = st.select_slider(
            "Energy prices", options=[0.0, 0.5, 1.0], value=base_cfg["energy_correction_weight"],
            format_func={0.0: "Published", 0.5: "Midpoint", 1.0: "CBS recomputation"}.get)
        method = st.radio("No-war price path", ["target", "pre_trend"],
                          format_func={"target": "2% a year from the war month",
                                       "pre_trend": "Each category's 24-month trend"}.get)
        survey_year = st.radio("Spending pattern", ["2020", "2015"], horizontal=True)
        take_up = st.slider("Energietoeslag take-up, poorest fifth", 0.0, 1.0, 0.55, 0.05)
        causal = st.slider("Causal share of the income–longevity gap", 0.0, 0.6, 0.25, 0.05)

    cfg = copy.deepcopy(base_cfg)
    for measure in cfg["compensation"]:
        if "take_up_by_quintile" in measure:
            measure["take_up_by_quintile"][0] = take_up
    cfg["human_cost"]["causal_share"]["central"] = causal
    results = run_all(cfg, inputs, method=method, energy_weight=energy_weight, survey_year=survey_year)
    lives = human_cost(cfg, inputs, results)

    with view:
        episode = st.radio("War", ["ukraine", "iran"], horizontal=True, key="episode",
                           format_func=lambda e: cfg["episodes"][e]["label"])
        result, life = results[episode], totals(lives[episode])
        summary = result.summary

        cols = st.columns(4)
        cols[0].metric("Poorest fifth, % of income", net_label(summary.at["Q1", "net_pct_income"]))
        cols[1].metric("Richest fifth, % of income", net_label(summary.at["Q5", "net_pct_income"]))
        cols[2].metric("Lifetimes lost (income route)", f"{life.at[('central', 'net'), 'lifetimes']:,.0f}")
        prevented = life.at[("central", "gross"), "lifetimes"] - life.at[("central", "net"), "lifetimes"]
        cols[3].metric("Prevented by support", f"{prevented:,.0f}")

        left, right = st.columns(2)
        with left:
            st.subheader("Who paid")
            fig = go.Figure()
            fig.add_bar(x=QUINTILE_NAMES, y=-summary["gross_pct_income"], marker_color=GREY_LIGHT,
                        customdata=summary["gross_pct_income"],
                        hovertemplate="%{x}: %{customdata:.2f}% before support<extra></extra>")
            fig.add_bar(x=QUINTILE_NAMES, y=-summary["net_pct_income"],
                        marker_color=[RED if v > 0 else GREY_DARK for v in summary["net_pct_income"]],
                        customdata=summary["net_pct_income"],
                        hovertemplate="%{x}: %{customdata:.2f}% after support<extra></extra>")
            fig.update_layout(barmode="overlay", bargap=0.35)
            st.plotly_chart(styled(fig, "% of income (down = lost)"), width="stretch")
        with right:
            st.subheader("What drove it")
            shares = (result.losses[result.losses["channel"].isin(cfg["direct_channels"])]
                      .groupby(["month", "channel"])["loss_share"].mean().unstack() * 100)
            fig = go.Figure()
            for channel, color in [("home_energy", GREY_DARK), ("food", RED), ("motor_fuel", GREY_LIGHT)]:
                fig.add_bar(x=shares.index.to_timestamp(), y=shares[channel], marker_color=color,
                            name=channel.replace("_", " "),
                            hovertemplate="%{x|%b %Y}: %{y:.2f}%<extra>%{fullData.name}</extra>")
            fig.update_layout(barmode="relative", bargap=0.1)
            st.plotly_chart(styled(fig, "% of monthly spending"), width="stretch")

        with st.expander("Numbers behind the charts"):
            table = summary[["gross_eur", "compensation_eur", "net_eur", "gross_pct_income", "net_pct_income",
                             "gross_pct_spending"]].rename(index=dict(zip(QUINTILES, QUINTILE_NAMES)))
            st.dataframe(table.round(2), width="stretch")
            st.dataframe(life.round(1), width="stretch")

    st.caption(DISCLAIMER + " Method and sources: see the story page and the repository.")


navigation = st.navigation(
    [st.Page(story, title="The story", default=True), st.Page(explorer, title="Model explorer", url_path="explorer")],
    position="top",
)
navigation.run()
