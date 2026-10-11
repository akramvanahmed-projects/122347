"""Interactive companion to the report: change the contested assumptions and watch the numbers move.

    streamlit run app.py
"""
from __future__ import annotations

import copy

import plotly.graph_objects as go
import streamlit as st

from warcost.analysis import human_cost, load_inputs, run_all
from warcost.config import QUINTILES, load_config
from warcost.health import totals

RED, GREY, GREY_LIGHT, INK = "#a50f15", "#9a9a9a", "#dcdcdc", "#1f1f1f"
QUINTILE_NAMES = ["Poorest fifth", "Second", "Middle", "Fourth", "Richest fifth"]

st.set_page_config(page_title="Hidden casualties", layout="wide")


@st.cache_data
def base_inputs() -> tuple[dict, dict]:
    return load_config(), load_inputs(load_config())


def layout(fig: go.Figure, height: int = 380, y_title: str = "") -> go.Figure:
    fig.update_layout(height=height, margin={"l": 10, "r": 10, "t": 30, "b": 10}, plot_bgcolor="white",
                      showlegend=False, font={"size": 13, "color": INK}, yaxis_title=y_title)
    fig.update_yaxes(gridcolor="#eeeeee", zerolinecolor=INK)
    return fig


base_cfg, inputs = base_inputs()

st.sidebar.header("Contested choices")
energy_weight = st.sidebar.select_slider(
    "Energy prices", options=[0.0, 0.5, 1.0], value=base_cfg["energy_correction_weight"],
    format_func={0.0: "Published (new contracts)", 0.5: "Midpoint", 1.0: "CBS recomputation"}.get)
method = st.sidebar.radio("No-war price path", ["target", "pre_trend"],
                          format_func={"target": "2% a year from the war month",
                                       "pre_trend": "Each category's 24-month trend"}.get)
survey_year = st.sidebar.radio("Spending pattern", ["2020", "2015"], horizontal=True)
take_up = st.sidebar.slider("Energietoeslag take-up, poorest fifth", 0.0, 1.0, 0.55, 0.05)
causal = st.sidebar.slider("Causal share of the income–longevity gradient", 0.0, 0.6, 0.25, 0.05)

cfg = copy.deepcopy(base_cfg)
for measure in cfg["compensation"]:
    if "take_up_by_quintile" in measure:
        measure["take_up_by_quintile"][0] = take_up
cfg["human_cost"]["causal_share"]["central"] = causal

results = run_all(cfg, inputs, method=method, energy_weight=energy_weight, survey_year=survey_year)
lives = human_cost(cfg, inputs, results)

st.title("Are there human casualties in the Netherlands from the wars in Ukraine and Iran?")
st.markdown("<div dir='rtl' style='font-size:1.1rem;color:#555'>"
            "هل يوجد ضحايا بشرية في هولندا بسبب الحرب في أوكرانيا والآن في إيران؟</div>", unsafe_allow_html=True)
st.caption(f"Prices to {inputs['prices'].index.max()}. Excess cost of food, home energy and motor fuel "
           "against a no-war path. Life-years are an equivalence derived from the income–longevity gradient.")

episode = st.radio("War", ["ukraine", "iran"], horizontal=True, key="episode",
                   format_func=lambda e: cfg["episodes"][e]["label"])
result, life = results[episode], totals(lives[episode])
summary = result.summary



def net_label(pct: float) -> str:
    return f"{pct:.1f}% of income lost" if pct >= 0 else f"{-pct:.1f}% of income ahead"


cols = st.columns(4)
cols[0].metric("Poorest fifth, after support", net_label(summary.at["Q1", "net_pct_income"]))
cols[1].metric("Richest fifth, after support", net_label(summary.at["Q5", "net_pct_income"]))
cols[2].metric("Lifetimes lost (equivalent)", f"{life.at[('central', 'net'), 'lifetimes']:,.0f}")
cols[3].metric("Prevented by support", f"{life.at[('central', 'gross'), 'lifetimes'] - life.at[('central', 'net'), 'lifetimes']:,.0f}")

left, right = st.columns(2)
with left:
    st.subheader("Who paid")
    fig = go.Figure()
    fig.add_bar(x=QUINTILE_NAMES, y=-summary["gross_pct_income"], marker_color=GREY_LIGHT, name="before support",
                hovertemplate="%{x}: %{customdata:.2f}% before support<extra></extra>",
                customdata=summary["gross_pct_income"])
    fig.add_bar(x=QUINTILE_NAMES, y=-summary["net_pct_income"], name="after support",
                marker_color=[RED if v > 0 else "#555555" for v in summary["net_pct_income"]],
                hovertemplate="%{x}: %{customdata:.2f}% after support<extra></extra>",
                customdata=summary["net_pct_income"])
    fig.update_layout(barmode="overlay", bargap=0.35)
    st.plotly_chart(layout(fig, y_title="% of income (down = lost)"), width="stretch")
with right:
    st.subheader("What drove it")
    shares = (result.losses[result.losses["channel"].isin(cfg["direct_channels"])]
              .groupby(["month", "channel"])["loss_share"].mean().unstack() * 100)
    fig = go.Figure()
    for channel, color in [("home_energy", "#555555"), ("food", RED), ("motor_fuel", GREY_LIGHT)]:
        fig.add_bar(x=shares.index.to_timestamp(), y=shares[channel], marker_color=color,
                    name=channel.replace("_", " "), hovertemplate="%{x|%b %Y}: %{y:.2f}%<extra>%{fullData.name}</extra>")
    fig.update_layout(barmode="relative", bargap=0.1)
    st.plotly_chart(layout(fig, y_title="% of monthly spending"), width="stretch")

with st.expander("Numbers behind the charts"):
    table = summary[["gross_eur", "compensation_eur", "net_eur", "gross_pct_income", "net_pct_income",
                     "gross_pct_spending"]].rename(index=dict(zip(QUINTILES, QUINTILE_NAMES)))
    st.dataframe(table.round(2), width="stretch")
    st.dataframe(life.round(1), width="stretch")
st.caption("Method, sources and limitations: see the README and reports/report.md in the repository.")
