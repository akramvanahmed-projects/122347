"""Hidden casualties — Streamlit dashboard.

    streamlit run app.py
"""
from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yaml

from src.human_cost import hardship, headline, income_ratio, life_cost
from src.model import ALL_GROUPS, QUINTILES, run_episode

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "processed"

# Palette: validated categorical slots + an ordinal blue ramp for quintiles.
WAR_COLORS = {"ukraine": "#2a78d6", "iran": "#eb6834"}
GROUP_COLORS = {"food": "#2a78d6", "home_energy": "#eb6834", "motor_fuel": "#1baf7a", "core": "#eda100"}
GROUP_LABELS = {"food": "Food", "home_energy": "Home energy", "motor_fuel": "Motor fuel", "core": "Everything else"}
QUINTILE_COLORS = dict(zip(QUINTILES, ["#0d366b", "#184f95", "#256abf", "#5598e7", "#86b6ef"]))
QUINTILE_LABELS = {"Q1": "Q1 (lowest 20%)", "Q2": "Q2", "Q3": "Q3", "Q4": "Q4", "Q5": "Q5 (highest 20%)"}
MEASURE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]

st.set_page_config(page_title="Hidden casualties — NL", layout="wide")


def style(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=40, b=8), legend_title_text="",
                      hoverlabel=dict(namelength=-1), font=dict(size=13))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)", zeroline=True, zerolinecolor="rgba(128,128,128,0.4)")
    return fig


@st.cache_data
def load():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    prices = pd.read_csv(DATA / "prices.csv", index_col="month")
    prices.index = pd.PeriodIndex(prices.index, freq="M")
    hh = pd.read_csv(DATA / "households.csv", index_col="quintile")
    return cfg, prices, hh


if not (DATA / "prices.csv").exists():
    st.error("No data yet. Run `python -m src.fetch` first.")
    st.stop()

cfg0, prices, hh = load()

# ------------------------------------------------------------------ sidebar
st.sidebar.header("Assumptions")
method = st.sidebar.radio("No-war price path", ["pre_trend", "target"],
                          format_func={"pre_trend": "Pre-war trend per category",
                                       "target": "ECB 2% target"}.get)
cfg = copy.deepcopy(cfg0)
cfg["counterfactual"]["pre_trend_months"] = st.sidebar.slider("Pre-trend window (months)", 12, 48,
                                                              cfg0["counterfactual"]["pre_trend_months"], 6)
months = [str(m) for m in prices.index if m > pd.Period(cfg0["episodes"]["ukraine"]["shock_start"], "M")]
cfg["episodes"]["ukraine"]["window_end"] = st.sidebar.select_slider(
    "Ukraine shock window ends", options=months, value=cfg0["episodes"]["ukraine"]["window_end"])
take_up = st.sidebar.slider("Energietoeslag take-up, lowest quintile", 0.0, 1.0, 0.55, 0.05)
for m in cfg["compensation"]:
    if "take_up_by_quintile" in m:
        m["take_up_by_quintile"][0] = take_up

has_income = hh["income_eur_year"].notna().all()
denom = "income" if has_income else "spending"
if not has_income:
    st.sidebar.info("No income data found — results are shown as % of household spending.")

results = {ep: run_episode(prices, hh, cfg, ep, method=method) for ep in ("ukraine", "iran")}
labels = {ep: cfg["episodes"][ep]["label"] for ep in results}

# ------------------------------------------------------------------ header
st.title("Are there human casualties in the Netherlands from the wars in Ukraine and Iran?")
st.markdown("<div dir='rtl' style='font-size:1.15rem;opacity:.75'>هل يوجد ضحايا بشرية في هولندا بسبب الحرب في أوكرانيا والآن في إيران؟</div>", unsafe_allow_html=True)
st.caption(f"How much of Dutch household {denom} two war price shocks took, by income quintile. "
           f"Prices: Eurostat HICP (NL), latest {prices.index.max()}. Spending: CBS Budgetonderzoek "
           f"{cfg['cbs']['survey_year']}.")

cols = st.columns(4)
for i, ep in enumerate(results):
    s = results[ep]["summary"]
    cols[2 * i].metric(f"{labels[ep]} — Q1 net loss", f"{s.at['Q1', f'net_pct_{denom}']:.1f}% of {denom}",
                       help=f"{int(s['months'].iloc[0])} months, after compensation")
    cols[2 * i + 1].metric(f"{labels[ep]} — Q5 net loss", f"{s.at['Q5', f'net_pct_{denom}']:.1f}% of {denom}")

tabs = st.tabs(["Headline", "Human cost", "Timeline", "What drove it", "Compensation", "Prices vs no-war", "Method"])

# ------------------------------------------------------------------ 1 headline
with tabs[0]:
    rows = []
    for ep, r in results.items():
        for q, row in r["summary"].iterrows():
            rows += [(labels[ep], QUINTILE_LABELS[q], "Gross", row[f"gross_pct_{denom}"], row["gross_eur"]),
                     (labels[ep], QUINTILE_LABELS[q], "Net of compensation", row[f"net_pct_{denom}"], row["net_eur"])]
    df = pd.DataFrame(rows, columns=["War", "Quintile", "Measure", "pct", "eur"])
    fig = px.bar(df, x="Quintile", y="pct", color="War", barmode="group", facet_col="Measure",
                 color_discrete_map={labels[k]: v for k, v in WAR_COLORS.items()},
                 custom_data=["eur"], labels={"pct": f"% of {denom} over the episode"})
    fig.update_traces(hovertemplate="%{x}<br>%{y:.2f}%<br>€%{customdata[0]:,.0f} per household<extra></extra>",
                      marker_line_width=0)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(style(fig, 420), width="stretch")
    st.markdown("**Reading it:** bars are the share of each quintile's "
                f"{denom} over the episode that went to war-excess prices. Lower-income households "
                "spend more of their budget on energy and food, so the same price shock costs them more.")
    with st.expander("Table"):
        st.dataframe(df.pivot_table(index="Quintile", columns=["War", "Measure"], values="pct").round(2))

# ------------------------------------------------------------------ 1b human cost
with tabs[1]:
    hc = cfg["human_cost"]
    st.markdown("### The human cost")
    st.caption("Order-of-magnitude estimates, not a death count. Income loss is translated into life expectancy "
               "using the CBS income–longevity gradient, scaled down for a temporary shock and for the share "
               "of the gradient that is causal. Ranges show low / central / high assumptions.")
    ep = st.radio("War", list(results), format_func=labels.get, horizontal=True, key="hc")
    r = results[ep]
    lc = life_cost(r["summary"], hh, hc, denom)
    h = headline(lc)
    hs = hardship(r["losses"], r["summary"], hh, hc, prices, cfg["cbs"]["survey_year"])

    def rng(col, basis="net", fmt="{:,.0f}"):
        lo, ce, hi = (h.at[(s_, basis), col] for s_ in ("low", "central", "high"))
        return fmt.format(ce), f"range {fmt.format(lo)} – {fmt.format(hi)}"

    k = st.columns(4)
    v, d = rng("lifetimes_equiv")
    k[0].metric("Full lifetimes lost (equivalent)", v, d, delta_color="off",
                help=f"Total life-years lost ÷ life expectancy ({hc['life_expectancy']:.0f} yrs). After compensation.")
    v, d = rng("life_years_total")
    k[1].metric("Life-years lost", v, d, delta_color="off")
    v, d = rng("healthy_years_total")
    k[2].metric("Healthy life-years lost", v, d, delta_color="off")
    hh_hard = hs["households"].sum()
    k[3].metric("Households in hardship", f"{hh_hard:,.0f}",
                f"lost ≥ {hc['hardship_food_months']:g} month of groceries", delta_color="off")

    saved = h.at[("central", "gross"), "lifetimes_equiv"] - h.at[("central", "net"), "lifetimes_equiv"]
    st.markdown(f"Without compensation the central estimate would be "
                f"**{h.at[('central', 'gross'), 'lifetimes_equiv']:,.0f} lifetimes** — government support "
                f"saved the equivalent of **{saved:,.0f}**.")

    c1, c2 = st.columns(2)
    d = lc[(lc.scenario == "central") & (lc.basis == "net")].copy()
    d["Quintile"] = d["quintile"].map(QUINTILE_LABELS)
    dl = d.melt(id_vars="Quintile", value_vars=["days_le_per_person", "days_hle_per_person"])
    dl["variable"] = dl["variable"].map({"days_le_per_person": "Life", "days_hle_per_person": "Healthy life"})
    fig = px.bar(dl, x="Quintile", y="value", color="variable", barmode="group",
                 color_discrete_sequence=["#2a78d6", "#eb6834"],
                 labels={"value": "days lost per person", "variable": ""},
                 title="Days lost per person (central)")
    fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:.2f} days<extra>%{fullData.name}</extra>")
    c1.plotly_chart(style(fig, 380), width="stretch")

    hs2 = hs.reset_index()
    hs2["Quintile"] = hs2["quintile"].map(QUINTILE_LABELS)
    fig = px.bar(hs2, x="Quintile", y="food_months_lost", title="War loss measured in months of groceries",
                 labels={"food_months_lost": "months of own food budget"},
                 color_discrete_sequence=["#2a78d6"])
    fig.add_hline(y=hc["hardship_food_months"], line_dash="dot", annotation_text="hardship threshold")
    fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:.2f} months<extra></extra>")
    c2.plotly_chart(style(fig, 380), width="stretch")

    ind = cfg["indicators"]
    ep_df = pd.DataFrame({"Energy poor": pd.Series(ind["energy_poverty_pct"]),
                          "Kept out by compensation": pd.Series(ind["saved_by_compensation_pct"])}).fillna(0)
    ep_df.index.name = "Year"
    fig = px.bar(ep_df.reset_index(), x="Year", y=["Energy poor", "Kept out by compensation"],
                 color_discrete_sequence=["#2a78d6", "#1baf7a"],
                 labels={"value": "% of households", "variable": ""},
                 title="Measured: households in energy poverty (CBS/TNO)")
    fig.update_traces(marker_line_width=2, marker_line_color="rgba(255,255,255,0.9)",
                      hovertemplate="%{x}<br>%{y:.1f}%<extra>%{fullData.name}</extra>")
    st.plotly_chart(style(fig, 360), width="stretch")
    st.caption(ind["source"] + ". 2023–2025 preliminary. Energy poverty fell during the Ukraine shock because "
               "support kept millions of households afloat, then rose again when it ended.")
    with st.expander("How the human cost is calculated"):
        st.markdown(f"""
- **Gradient:** Q5 lives {hc['le_gap_years']} years longer than Q1 (healthy: {hc['hle_gap_years']} years), with an income
  ratio of about {income_ratio(hh, hc):.1f}× between them → years of life per unit of log income.
- **Temporary shock:** the gradient builds over ~{hc['exposure_years']} adult years, so a {r['summary']['months'].iloc[0]}-month
  shock gets {r['summary']['months'].iloc[0]}/12 ÷ {hc['exposure_years']} of it.
- **Causality:** only part of the gradient is caused by income: low {hc['causal_share']['low']:.0%},
  central {hc['causal_share']['central']:.0%}, high {hc['causal_share']['high']:.0%}.
- **Full lifetimes** = total life-years lost ÷ {hc['life_expectancy']:.0f}. It is an equivalence, not a count of deaths.
- **Hardship:** households whose net loss exceeds {hc['hardship_food_months']:g} month(s) of their own grocery budget
  (quintile averages, so it moves in steps of 20% of households).
""")
        st.dataframe(lc.pivot_table(index="quintile", columns=["scenario", "basis"],
                                    values="days_le_per_person").round(2))

# ------------------------------------------------------------------ 2 timeline
with tabs[2]:
    st.markdown("Monthly war-excess cost as % of spending, aligned on months since each shock.")
    frames = []
    for ep, r in results.items():
        t = r["losses"].groupby(["month", "quintile"])["loss_share_spend"].sum().reset_index()
        anchor = pd.Period(cfg["episodes"][ep]["shock_start"], "M")
        t["months_since"] = t["month"].apply(lambda m: (m - anchor).n)
        t["War"] = labels[ep]
        frames.append(t)
    tl = pd.concat(frames)
    tl["pct"] = tl["loss_share_spend"] * 100
    tl["Quintile"] = tl["quintile"].map(QUINTILE_LABELS)
    tl["month"] = tl["month"].astype(str)
    fig = px.line(tl, x="months_since", y="pct", color="Quintile", facet_col="War",
                  color_discrete_map={QUINTILE_LABELS[q]: c for q, c in QUINTILE_COLORS.items()},
                  custom_data=["month"],
                  labels={"months_since": "Months since shock", "pct": "% of monthly spending"})
    fig.update_traces(line_width=2, hovertemplate="%{customdata[0]}: %{y:.2f}%<extra>%{fullData.name}</extra>")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(style(fig.update_layout(hovermode="x unified"), 420), width="stretch")

# ------------------------------------------------------------------ 3 drivers
with tabs[3]:
    ep = st.radio("War", list(results), format_func=labels.get, horizontal=True, key="drv")
    d = results[ep]["losses"].groupby(["quintile", "group"])["loss_eur"].sum().reset_index()
    d["Category"] = d["group"].map(GROUP_LABELS)
    d["Quintile"] = d["quintile"].map(QUINTILE_LABELS)
    fig = px.bar(d, x="Quintile", y="loss_eur", color="Category",
                 category_orders={"Category": [GROUP_LABELS[g] for g in ALL_GROUPS]},
                 color_discrete_map={GROUP_LABELS[g]: c for g, c in GROUP_COLORS.items()},
                 labels={"loss_eur": "€ per household over the episode"})
    fig.update_traces(marker_line_width=2, marker_line_color="rgba(255,255,255,0.9)",
                      hovertemplate="%{x}<br>€%{y:,.0f}<extra>%{fullData.name}</extra>")
    st.plotly_chart(style(fig, 420), width="stretch")
    st.caption("Negative 'Everything else' means non-energy prices rose less than their pre-war trend.")

# ------------------------------------------------------------------ 4 compensation
with tabs[4]:
    comp = pd.concat([r["comp"].assign(War=labels[ep]) for ep, r in results.items()])
    comp["Quintile"] = comp["quintile"].map(QUINTILE_LABELS)
    fig = px.bar(comp, x="Quintile", y="eur", color="measure", facet_col="War",
                 color_discrete_sequence=MEASURE_COLORS, labels={"eur": "€ per household", "measure": ""})
    fig.update_traces(marker_line_width=2, marker_line_color="rgba(255,255,255,0.9)",
                      hovertemplate="%{x}<br>€%{y:,.0f}<extra>%{fullData.name}</extra>")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_layout(legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(style(fig, 480), width="stretch")
    st.dataframe(pd.concat({labels[ep]: (r["summary"]["compensation_eur"] / r["summary"]["gross_eur"] * 100)
                            .rename("% of gross loss offset") for ep, r in results.items()}, axis=1).round(1))
    st.caption("2023 energy price ceiling is already inside the price index and therefore not listed here. "
               "Amounts and take-up rates are set in config.yaml.")

# ------------------------------------------------------------------ 5 prices
with tabs[5]:
    c1, c2 = st.columns(2)
    ep = c1.radio("War", list(results), format_func=labels.get, horizontal=True, key="px")
    grp = c2.selectbox("Category", ALL_GROUPS, format_func=GROUP_LABELS.get)
    anchor = pd.Period(cfg["episodes"][ep]["shock_start"], "M")
    win = slice(anchor - 24, results[ep]["gaps"].index.max())
    pdf = pd.DataFrame({"Actual": prices.loc[win, grp], "No-war path": results[ep]["cf"].loc[win, grp]})
    pdf.index = pdf.index.to_timestamp()
    fig = go.Figure()
    fig.add_scatter(x=pdf.index, y=pdf["No-war path"], name="No-war path",
                    line=dict(color="#8a8984", width=2, dash="dash"))
    fig.add_scatter(x=pdf.index, y=pdf["Actual"], name="Actual", line=dict(color=WAR_COLORS[ep], width=2),
                    fill="tonexty", fillcolor="rgba(235,104,52,0.12)")
    fig.add_vline(x=anchor.to_timestamp(), line_width=1, line_dash="dot")
    fig.update_layout(hovermode="x unified", yaxis_title="Price index")
    st.plotly_chart(style(fig, 420), width="stretch")

# ------------------------------------------------------------------ 6 method
with tabs[6]:
    st.markdown((ROOT / "README.md").read_text().split("## 3. Run it")[0])
    st.markdown("**Household inputs used**")
    st.dataframe(hh.style.format({c: "{:.1%}" for c in hh.columns if c.startswith("share_")}
                                 | {"spending_eur_year": "€{:,.0f}", "income_eur_year": "€{:,.0f}"}))
