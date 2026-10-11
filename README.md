# Are there human casualties in the Netherlands from the wars in Ukraine and Iran?
<div dir="rtl">هل يوجد ضحايا بشرية في هولندا بسبب الحرب في أوكرانيا والآن في إيران؟</div>

**Research question.** No bombs fell on the Netherlands, but the price shocks of the
Russia–Ukraine war (2022–23) and the Iran war (2026–) took income from every household.
How much, from whom, through which spending, how much did government support give
back — and what does that income loss mean in **life-years, healthy life-years,
households pushed into hardship, and "full lifetimes lost" equivalents**?

**Why it's a good portfolio project.** It combines public microdata-based statistics
(CBS budget survey), monthly price indices (Eurostat HICP), a counterfactual model,
distributional analysis and a policy layer — and it is about a live event.

---

## 1. Method (one paragraph per step)

**1.1 War-excess prices.** For each spending group *g* (food, home energy, motor fuel,
everything else) we build a *no-war* price path from the month before each shock,
growing at its pre-war trend (or the ECB 2% target — switchable). The excess price
gap is `gap_g(t) = I_g(t) / CF_g(t) − 1`.

**1.2 Quintile-specific exposure.** Low-income households spend a bigger share on
energy and food. Using CBS Budgetonderzoek 2020 spending shares `w_{q,g}` per
income quintile *q*, the loss as a share of spending is
`L_q(t) = Σ_g w_{q,g} · gap_g(t)` — a first-order Laspeyres approximation (no
substitution, so it is an *upper bound* on the welfare loss).

**1.3 From spending to income.** Monthly euro loss = `L_q(t) × monthly spending_q(t)`,
where 2020 spending is uprated with the all-items index. Summed over the episode and
divided by disposable income gives **% of annual income lost**. Low quintiles spend
close to (or above) 100% of income, high quintiles much less — that amplifies the gap.

**1.4 Compensation.** Transfers not inside the price index (Nov–Dec 2022 discount,
energietoeslag, 2026 commuting allowance) are subtracted per quintile → **net loss**.
The 2023 energy price ceiling is already inside the price index, so it is not
double-counted.

**1.5 Human cost.** CBS reports the top income quintile lives ~8.5 years longer
(~18 healthy years) than the bottom one. That gradient, per log-point of income, is
scaled for a temporary shock (shock years ÷ ~60 adult years) and for the share that
is causal (10% / 25% / 50%). Days lost per person × population = life-years lost;
÷ life expectancy (82) = **full lifetimes lost (equivalent)** — an equivalence, not a
death count. Hardship = households whose net war loss exceeds a month of their own
grocery budget. Measured energy-poverty figures (CBS/TNO) are shown alongside.

**1.6 Sensitivity.** Every assumption (counterfactual method, window end, take-up)
lives in `config.yaml` and is adjustable in the dashboard sidebar.

## 2. Data sources

| What | Source | ID |
|---|---|---|
| Monthly price index by COICOP, NL | Eurostat HICP | `prc_hicp_midx` |
| Spending shares by income quintile (2020) | CBS StatLine | `85420NED` |
| Spending in € per household by income group (2020) | CBS StatLine | `85419NED` |
| Disposable income by quintile | CBS StatLine | `83932NED` (verify) |
| Compensation measures | Rijksoverheid | see `config.yaml` |

All via open APIs (CC-BY 4.0). If CBS label matching fails, run
`python -m src.fetch --templates` and fill `data/manual/household_budget.csv`
from the CBS StatLine website (shares as fractions, e.g. 0.12).

## 3. Run it

```bash
pip install -r requirements.txt
python -m src.fetch          # downloads data → data/processed/*.parquet
pytest -q                    # checks the model maths on a synthetic fixture
streamlit run app.py
```

## 4. Dashboard pages

1. **Headline** — % of income lost per war, per quintile, gross vs net of compensation.
1. **Human cost** — lifetimes lost (equivalent), life-years, healthy life-years, hardship, energy poverty.
2. **Timeline** — monthly loss rate per quintile, both wars on one axis (months since shock).
3. **What drove it** — stacked contribution of food / home energy / motor fuel / other.
4. **Compensation** — how much each measure returned, per quintile.
5. **Methodology & limitations.**

## 5. Limitations (put these in your write-up — it shows maturity)

- Spending weights are from 2020; behaviour changed after 2022 (people cut gas use).
- HICP energy prices tracked new contracts; households on fixed contracts felt the
  shock later (CBS changed its energy method in 2023 for this reason).
- HICP excludes owner-occupied housing; mortgage-rate effects are out of scope.
- Not all inflation after the shock is "caused by" the war — the counterfactual is
  a modelling choice. Show both counterfactuals.
- Wage indexation and pension indexation partly offset losses; an extension could
  add CBS CAO-wage data to estimate *real* income loss.

## 6. Possible extensions

- Add CAO-wages (CBS 82838NED-family tables) for real-wage loss.
- Region view with CBS energy consumption per municipality.
- Compare with Belgium/Germany via Eurostat HBS quintile shares.
