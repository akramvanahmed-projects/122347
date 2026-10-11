# Referee report on version 0.1

This review scores the project as it stood before the October 2026 revision (one Streamlit file, synthetic tests, data never fetched), then lists what the revision fixed and what it did not. Scores are out of 10.

| Part | Method | Rigour | Argument | Clarity | Code | Reproducibility |
|---|---|---|---|---|---|---|
| Price-shock counterfactual | 5 | 4 | 4 | 6 | 6 | 3 |
| Distribution by income fifth | 5 | 3 | 3 | 6 | 5 | 3 |
| Compensation layer | 4 | 3 | 4 | 6 | 6 | 4 |
| Human-cost layer | 3 | 2 | 2 | 5 | 6 | 4 |
| Pipeline and code | – | – | – | 6 | 5 | 2 |
| Dashboard and text | – | – | 4 | 6 | 5 | 3 |

Reproducibility scores low throughout because version 0.1 had never run on real data. Its CBS parser matched Dutch labels that did not exist, its Eurostat dataset stopped in December 2025, and it would have crashed on pandas 3. Every number it displayed came from a synthetic fixture.

## Five critical problems

**1. The headline attributed all excess inflation to the war.** Version 0.1 counted "core" inflation (services, rents, durables) above a pre-war trend as war damage. In 2022 that channel was larger than food and energy combined: €2,532 per household against €1,872. Most of it reflects reopening after Covid, a record-tight labour market and rent indexation. The revision removes core from the headline and reports it only as a sensitivity row, with the reason stated.

**2. The energy price series was wrong in a way the author did not check.** Until June 2023, Dutch energy prices in the HICP were measured from new contracts only. CBS has published how far that overstated 2022 and understated early 2023. Version 0.1 ignored this, and so did the first draft of the revision, which assumed the correction would lower the Ukraine bill. It raises it, because anchoring at February 2022 pushes the delayed pass-through of the autumn 2021 spike into the war window. The two series are biased in opposite directions. The revision uses their midpoint and reports both as bounds (poorest fifth, gross: 2.8% to 4.6% of income).

**3. "The poor lost most" was an artefact of the denominator.** As a share of spending, the Ukraine loss is 2.7% to 3.1% for every fifth. As a share of income it runs from 1.25% to 3.7%, because the poorest fifth's survey spending is 1.34 times its registered income. Version 0.1 showed only the income version and wrote the conclusion into the dashboard caption. The revision reports both and explains the gap. It still cannot say how much of the 1.34 is dissaving and how much is income the register misses.

**4. The human-cost layer converted correlation into causation and hid it in a slider.** The CBS income–longevity gap is cross-sectional. Applying it to a 22-month shock requires two scaling assumptions: the causal share and the exposure period. No data identifies either, and the result is linear in both. Version 0.1 also counted "households in hardship" by assigning every household in a fifth that fifth's average loss, an ecological fallacy that produced "8.3 million households in hardship" on test data. The revision drops the headcount, reports a range of 45 to 226 lifetimes rather than a point, names the equivalence as an equivalence in every chart, and cites counter-evidence (Ruhm, 2000). The layer is still the weakest part of the project and should be read as an order of magnitude.

**5. The compensation result rests on one unsourced number.** Whether the poorest fifth gained or lost depends on energietoeslag take-up, which version 0.1 set at 55% without a source. The revision computes the break-even (32%) and plots the whole curve, which turns a hidden assumption into a visible one. The SZW implementation monitor puts municipal reach at about 90% of eligible households in 2022 and 86% in 2023, so the open question is now narrower: what share of the poorest fifth was eligible. Above roughly 36%, the fifth came out ahead on average.

## Smaller issues fixed in the revision

- Imputed rent (11–19% of spending in the upper four fifths) was in the spending base and was priced with core inflation. It is not a cash outlay and HICP has no price for it.
- Prices started in 2017, so the 2015 survey could not be uprated. The model silently produced zeros. It now raises an error.
- The pre-trend counterfactual was offered as an equal alternative. For energy in 2022 it extrapolates the 2021 run-up and concludes the war lowered energy costs. It stays available, but labelled as a stress test.
- Persons per fifth were assumed equal (2.1 per household). CBS data gives 1.1 in the poorest fifth and 3.4 in the richest, which matters when converting per-person days into national totals.
- The life-expectancy gradient used household income ratios. The CBS studies rank by standardised (equivalised) income, which the revision now uses.

## Still open

- No mortality channel for cold homes, the most plausible direct route from an energy shock to deaths.
- Wage, benefit and pension indexation is not netted off, which overstates net losses for 2023.
- Quintile averages. Household microdata (CBS remote access) would allow real headcounts.
- The CBS energy research series is transcribed from an article. A StatLine source should replace it if one exists.

## Figure design notes

Each figure started from the question of what the data feels like, then took the strongest idea that kept axes honest.

1. **Who paid.** Bold: losses hang below an "income line" like a wound, with grey showing the part support closed (chosen). Moderate: dumbbells from gross to net per fifth. Conservative: grouped bars, before and after.
2. **Size over time.** Bold: Ukraine as a grey wave with Iran as a red ripple, aligned on months since the war began (chosen). Moderate: twin lines on a common axis. Conservative: small multiples, one per war.
3. **The price gap.** Bold: actual against no-war path with the gap filled red, so the bill is literally the shaded area (chosen). Moderate: excess-percentage lines. Conservative: a table of peak gaps.
4. **What drove it.** Bold: a relay, energy handing over to food, as stacked monthly bars with only food in red (chosen). Moderate: two lines crossing in January 2023. Conservative: annual totals by category.
5. **Human cost.** Bold: one dot per 82-year lifetime, red for lost, open for prevented by support, the same dot size for both wars (chosen). Moderate: a range bar per war. Conservative: point estimates with error bars.
6. **Support.** Bold: energy poverty with the "would have been" share hatched above the bars during the support years, beside the break-even curve (chosen). Moderate: a single line with the support period shaded. Conservative: a table.

## Review of the October 2026 additions

The story page and the "Beyond the household budget" section widen the project from a price model to a social account. That makes it more interesting and more exposed.

- **Attention is the largest number in the project and rests on the softest input.** The share of adults who followed and worried is measured (87% and 90%, I&O for NOS). The minutes per day are assumed (15 then 5). The result scales one-for-one with them, so 1,180 waking lifetimes could as easily be 400 or 3,000. The page makes the assumption adjustable rather than hiding it, which is the right call, but no headline should quote the number without the dial next to it.
- **Waking lifetimes and health lifetimes are not the same unit.** Putting them on one axis invites the reader to add them. The page states that time spent following a war is not lost the way a life is. A stricter version would value attention in euros using a wage rate, which is how time-use economics normally prices it.
- **The death figure is presented without attribution, deliberately.** November 2022's 1,400 excess deaths are shown because readers will ask, and labelled "can't tell" because CBS attributes 2022 excess mortality mainly to flu and covid. A proper study would regress weekly excess deaths on indoor temperature or gas use, controlling for flu and covid incidence. That is the most valuable extension left.
- **Several facts come from news reports of CBS releases rather than StatLine tables** (gas use, holidays, consumer confidence, money worries). They are traceable to CBS, but the confidence and gas series should be pulled from StatLine by the pipeline so they refresh with the rest.
- **Verdicts are judgement.** The "Can we blame the war?" scale is the author's reading of the evidence, stated per chapter with its reason. It is a communication device, not a statistical test.

## Review of the casualty ledger

- **The cold-death estimate imports a US elasticity.** It is peer-reviewed and the mechanism (people heat less, cardiovascular and respiratory deaths rise) is well documented, but Dutch housing, climate and the size of the 2022 shock differ from the US 2000–2010 sample. The 95% interval (170 to 2,200) is wide for a reason. A Dutch estimate from weekly deaths, regional gas prices and indoor temperatures would replace it.
- **Disability weights for worry are borrowed, not measured.** Financial worry is not a GBD health state. The central weight (0.010) is a third of mild anxiety; the upper bound is the full mild-anxiety weight. The worn-down-years total (270 to 1,580 lifetimes) moves one-for-one with this choice and dominates the "all lives" figure. That is stated wherever the total appears.
- **Adding deaths and life-year equivalents is a convention, not a fact.** The ledger adds them because the question was asked in those terms, and labels the sum "dead + equivalents". Attention is kept in a separate unit and never added.
- **Wounds overlap.** The 17.5 million light wounds exceed the adult population because people appear in several groups. The page says so next to the number.
- **The serious-wounded count leans on the take-up assumption.** About 855,000 of the 904,000 serious wounds are poorest-fifth residents without the €1,300 payment, which rests on the 55% take-up used throughout.

## Review of the common time frame

- **Every number now covers one period**, March 2022 to the latest month with price data, for both wars. This was the right call: the earlier version mixed a 22-month bill, one winter of deaths, one year of attention and single-year survey changes, and readers could not tell what to add to what.
- **The aftermath rule is the new judgement call.** After December 2023 each category's excess is held at its Oct–Dec 2023 level. That counts the price level the war left behind but no later inflation. It still ignores wage and benefit indexation, which by 2024 had largely caught up, so the post-2023 bill is an upper bound.
- **The energy correction now carries more weight.** The level gap between the published and recomputed CBS energy series carries into every later month. On the published index, home energy after 2023 is a saving and the three later winters add zero deaths; on the recomputation, both are larger. The midpoint is kept, and the spread is reported.
- **Unmeasured years count zero.** Money worries after 2024, holidays after 2023 and thermostat behaviour after the first winter are not yet published. That understates the later part of the period; it does not overstate it.
