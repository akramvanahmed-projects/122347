# Hidden casualties: what two war price shocks cost Dutch households

The Russia–Ukraine war cost Dutch households €15.5 billion in excess spending on food, home energy and motor fuel between March 2022 and December 2023. Support returned €5.9 billion. After support, the middle three income fifths lost between 1.5% and 1.7% of their disposable income, and the richest fifth 1.1%. The poorest fifth came out 1.9% ahead, but only on average and only if enough of them claimed the energietoeslag. Translated into life expectancy, the net loss equals about 113 full lifetimes (range 45 to 226). Counted as casualties, the Ukraine shock left about 1,200 estimated deaths from the cold, more than 900,000 people seriously wounded and about 1,850 lives lost in total once life-expectancy equivalents are added (range 490 to 4,000). The Iran war has so far cost €78 per household and the equivalent of 3 lifetimes. Its price shock has reached the petrol pump but not, as of August 2026, the gas meter.

These numbers come from a deliberately narrow definition of "war cost", and most of this report is about why it is narrow. The second half widens the lens to what money does not capture: the heating turned down, the holiday not taken, the record low in consumer confidence, and the attention the war absorbed. It then assembles everything into a casualty ledger of the dead, the wounded and the lost hours, and ends with who carried the load.

A companion story page presents the same results visually: `docs/index.html` in the repository.

## What is measured

A war shock raises some prices above where they would otherwise have been. For each category we take the price level in the month the war began and let it grow at 2% a year, the ECB target. The gap between actual prices and that path is the excess price. Prices are Eurostat's monthly HICP for the Netherlands (`prc_hicp_minr`, ECOICOP 2, 2015=100).

Only three categories count towards the headline: food, home energy and motor fuel. Those are the channels through which an energy-supply war reaches households directly. Excess inflation in everything else, mostly services and rents, is reported separately and kept out of the headline. In 2022 that "core" inflation had too many other causes to pin on the war: post-Covid reopening, the tightest Dutch labour market in decades, and indexation of rents. In 2026 Dutch services prices were already rising 4.2% a year in February, before the strikes (CBS, reported by NL Times, 2026), so a 2% path would blame Iran for a trend that predates it. Including core would add €2,532 per household to the Ukraine bill, more than doubling it. We do not believe that number.

Excess prices are weighted by what each income fifth buys, using the CBS budget survey of 2020 (StatLine 85420NED for shares, 85419NED for euro amounts). Owner-occupiers' imputed rent is removed from the spending base, because nobody pays it and HICP does not price it. Euro losses are compared with disposable income per fifth from CBS 83932NED, uprated by the all-items index after 2024. Compensation that does not appear in prices is subtracted per fifth: the €190 monthly discount in November and December 2022, and the €1,300 energietoeslag in 2022 and 2023. The 2023 price ceiling and the 2022 fuel excise cut are already inside the price index and are not counted twice (CBS, 2022).

## The Ukraine shock

The shock arrived in two waves. Home energy came first. On the published index it peaked 96% above the no-war path in October 2022, then fell to 19.5% below it by late 2023, once the price ceiling and falling wholesale gas pulled it down. Food came second and never retreated. It was still 14% above its path in December 2023. From January 2023 food was the larger cost every month (figure 4). Averaged across households, the monthly excess peaked at 4.8% of spending in December 2022 and was still 2.5% when the window closed (figure 2).

Over 22 months, food cost the average household €1,073 and home energy €862 (midpoint of the two energy series, see below). Motor fuel saved €62, mostly thanks to the excise cut.

The distribution depends on the denominator. As a share of spending the loss is nearly flat: 2.9% for the poorest fifth, 3.1% for the middle, 2.7% for the richest. The poorest fifth spends more of its budget on home energy (5.5% against 3.7%), but less on motor fuel (1.7% against 3.0%), and the two roughly cancel. As a share of income, the same losses look steeply regressive: 3.7% for the poorest fifth against 1.25% for the richest. The difference comes from one fact in the CBS data. In 2020 the poorest fifth spent €19,900 against a registered disposable income of €14,850, a ratio of 1.34. Part of that is real dissaving by students and pensioners drawing on assets. Part is probably income the survey misses [citation needed]. Either way, "the poor lost the most" is a statement about the denominator, not about who faced the higher prices.

Support changes the picture more than prices do. Every household received €380. Households near the social minimum could claim €1,300 in each of two years; most municipalities set the limit at 120% of the minimum and about a fifth at 130%. If 55% of the poorest fifth claimed both, the fifth as a whole ended €601 ahead. The break-even take-up is 32% (figure 6). Municipalities estimate they reached about 90% of eligible households in 2022 and 86% in 2023 (SZW, 2024). At that reach, 55% take-up across the poorest fifth means roughly 60–64% of its households were eligible, and the fifth only falls below break-even if fewer than about 36% were. The eligible share is not published by income fifth [citation needed], so this remains the most important unverified number in the project, but the reach figures make the gain more likely than not. The average also hides the people who did not claim. A poorest-fifth household that missed the energietoeslag still lost about €830, and in the bottom fifth that is roughly 5% of a year's income.

The CBS/TNO energy-poverty monitor points the same way. The share of households in energy poverty fell from 6.8% in 2021 to 4.1% in 2022 and 3.7% in 2023. Without support it would have been 5.9% and 8.0%. Once payments stopped, it went back to 6.0% in 2024 and stayed there in 2025.

## The Iran shock so far

Six months in (March to August 2026), Dutch motor fuel prices sit 15% above their no-war path. Food sits 1.3% below its path, and home energy only 2.6% above. Most households are on contracts that will reprice over the coming year, so the energy channel has barely started. The excess so far is €78 per household, €0.6 billion nationally, and 0.4% of monthly spending at the latest reading. That is a ripple next to Ukraine's wave (figure 2). It is also the one result in this project that will certainly change. The Action re-runs the model every month.

The distribution runs the other way from Ukraine: as a share of spending the richest fifth loses 0.45% and the poorest 0.19%, because fuel is the channel and car ownership rises with income. The 2026 commuting-allowance increase is modelled with rough per-fifth amounts [citation needed], so the net Iran figures are less reliable than the gross ones.

## From income to life-years

CBS reports that the richest fifth lives about 8.5 years longer than the poorest (9 for men, 8 for women) and spends about 18 more years in good health [citation needed: income-only study year]. Read naively, that gradient implies that every percentage point of income lost costs life. Read carefully, it implies much less. Three adjustments do the work.

First, the gradient is cross-sectional and mostly not causal. Illness lowers income at least as much as low income causes illness, and education, occupation and health behaviour drive both. We credit 25% of the gradient to income, with 10% and 50% as bounds. These shares are judgement calls [citation needed]. Second, the gradient builds over a lifetime of income differences, so a 22-month shock gets 22 months' worth of a 60-year exposure. Third, the gradient is expressed per log-point of standardised income, using the Q5/Q1 ratio of 4.8 in the 2024 CBS data. That assumes the same slope at every income level. US data show life expectancy rising steadily across the whole income distribution rather than only at the bottom (Chetty et al., 2016), which makes a single slope defensible but not proven for the Netherlands. The CBS gap is also measured on income and wealth together, while our ratio uses income alone, which steepens the slope somewhat.

The result for Ukraine, after support, is 9,259 life-years and 19,606 healthy life-years across 18 million people. That works out to 0.19 days of life per resident. Divided by life expectancy, it equals 113 full lifetimes. Without support it would have been 185 (figure 5). For Iran so far: 3.

These are equivalences, not deaths. Nobody in this model dies. The figure says that a loss of life expectancy spread thinly over everyone adds up to the same total as about 113 complete lives. There is also serious evidence pointing the other way. In US state-level data, mortality falls during recessions (Ruhm, 2000), because people drive less, drink less and work less dangerously. A price shock is not a recession, but the sign of the short-run effect is not settled. The most direct mortality channel, cold homes during the winter of 2022–23, is not modelled here at all. The next section explains why.


## Beyond the household budget

Money is the part of a war shock that statistics capture best. The rest has to be assembled from scattered sources, and for most of it the honest answer to "was this the war?" is "partly" or "we cannot tell". Each item below says which.

**The cold.** Dutch households burned about a quarter less gas in 2022 than in 2021, and total national use fell to 31 billion cubic metres, the lowest since 1972. Corrected for a mild winter, use was still 15% lower, and CBS names price as the main driver (CBS via NOS, 2023). Seven in ten households with a gas boiler set the thermostat to 19 °C instead of 21 (Milieu Centraal), and smart-thermostat data put the average living room at 18 °C that winter (tado; both via Wynia's Week, 2023). Whether the cold killed anyone is the open question of this project. In November 2022 about 1,400 more people died than expected, 10% above the norm, half of them in vulnerable groups such as nursing-home residents (CBS via ANP, December 2022). CBS attributes most of 2022's excess mortality to flu and covid-19 (CBS via ANP, January 2023), and no Dutch study separates out cold homes. The gas cut is clearly war-driven. The deaths cannot be assigned. *Verdict: can't tell.*

**The kitchen.** Food is the channel that stayed. It cost the average household €1,073 over 22 months and was still 14% above its no-war path at the end of 2023. Food banks served almost 200,000 people in 2022; by 2025 that had fallen to just over 155,000 and was rising again (Voedselbanken Nederland via NOS, 2026). Energy, fertiliser and grain push food prices up, but so did wages, retail margins and avian flu in the same period, so the food figure is an upper bound on the war's share. *Verdict: partly.*

**The holiday.** In 2023, 19.2% of people aged 15 and over took no holiday, against 18.5% in 2019. Of those who stayed home, 27.6% said they could not afford it. The gap by income is wide: 38% of the lowest-income quarter took no holiday, against 8% of the highest (CBS, 2024). Covid emptied travel in 2020 and the recovery hides any war effect in 2022. For Iran the link is direct: in April 2026 KLM scrapped 160 flights over the May holiday as kerosene prices rose (NL Times, 2026). *Verdict: can't tell for 2022, yes for 2026.*

**The nerves.** Consumer confidence fell to −59 in September and October 2022, the lowest since CBS began the series in 1986, against a twenty-year average of about −10 (CBS, 2022). In the same month Nibud reported that one in three households could barely make ends meet and that calls to its helpline ran 1.5 to 2 times above normal (Nibud via NL Times, 2022). The share of people worried about their finances rose from 23% in 2021 to almost 30%, and about 40% among the lowest earners (CBS via ANP, 2023). After the Iran strikes, confidence dropped from −24 in February 2026 to −46 in May (CBS, 2026). The timing matches both wars, but CBS does not attribute the drops to a cause. *Verdict: partly.*

**The attention.** In the first week of March 2022, 87% of Dutch adults followed the war, 90% were worried about it, and 44% feared a nuclear attack (I&O Research for NOS, n = 2,132). The eight o'clock news drew 2.3 million viewers on 7 March (TV Gids). No one has measured how many minutes the country spent following, discussing and worrying about the war, so we assume it: 15 extra minutes a day per follower for the first three months and 5 a day for the rest of the year. Applied to about 12.4 million adult followers, that is 565 million hours. Divided by a waking lifetime (82 years of 16 waking hours, about 479,000 hours), it equals about 1,180 waking lifetimes, ten times the income-based life-expectancy estimate above. The minutes are the weakest input in this report, and the story page lets the reader change them. Time spent understanding a war is not lost in the way a life is; much of it was civic attention, and some turned into donations and housing for refugees. Government time is not counted because neither cabinet nor parliament publishes hours by topic; the Speaker of the House described 2022 only as a year of "many debates" on Ukraine (Tweede Kamer, 2022). *Verdict: yes for the cause, assumed for the size.*

## The casualty ledger

The project's question was whether the wars caused human casualties in the Netherlands. Answering it in a military register means counting three things separately: the dead, the wounded, and, because a war that is followed on screens also consumes time, the hours.

**The dead: cold.** No Dutch death certificate names energy prices, so the count has to be estimated. Chirakijja, Jayachandran and Ong (2023) estimate from US winters that a 1% rise in the winter heating price raises all-cause mortality by 0.032% (standard error 0.014). In the Dutch heating season of October 2022 to March 2023, home energy cost on average 46% more than its no-war path, using the same midpoint of published and recomputed CBS energy prices as the cost model. About 82,000 deaths were expected in those six months, a figure derived from CBS's weekly expected-death series (3,050 to 3,460 a week in December and January). The product is about **1,200 deaths**, with a range of 170 to 2,200 from the 95% interval of the elasticity. For scale: CBS counted about 4,800 deaths above expected between late November 2022 and January 2023, attributing most of 2022's excess to flu and covid-19, and The Economist estimated 68,000 energy-price deaths across Europe that winter, which scales to a figure of similar magnitude for the Netherlands. Transferring a US elasticity to Dutch housing is the weakest step. Dutch homes are better insulated, but Dutch households cut gas use far more sharply.

**The dead: life expectancy.** The income channel described above adds 113 lifetime equivalents (45–226).

**The wounded.** We count people whose quality of life the war damaged, separately from deaths, and price the damage in healthy life-years with disability weights from the Global Burden of Disease study (mild anxiety 0.030, moderate 0.133). Financial worry is not a GBD health state; we give it a third of the mild-anxiety weight and use the full weight as an upper bound. Serious hardship gets twice the mild weight.

| Group | Severity | People | Weight (range) | Years | Healthy years lost |
|---|---|---|---|---|---|
| Needed food aid | serious | 49,500 | 0.06 (0.03–0.133) | 1.0 | 3,000 |
| Poorest fifth without the €1,300 payment | serious | 854,806 | 0.01 (0.005–0.03) | 1.83 | 15,600 |
| New money worries | light | 994,000 | 0.01 (0.005–0.03) | 1.5 | 14,900 |
| Worried a lot about the war | light | 5,538,000 | 0.01 (0.005–0.03) | 0.1667 | 9,200 |
| Skipped a holiday | light | 255,000 | 0.005 (0.0025–0.015) | 1.0 | 1,300 |
| Lived in a colder home | light | 10,710,000 | 0.0 (0.0–0.0) | 0.5 | 0 |

People appear in several rows, so the counts are wounds, not persons. Together the groups lose about 44,000 healthy years, or **540 lifetime equivalents** (270–1,580). The serious wounded number about **904,306**; the light wounds about 17.5 million. The colder-home group carries no weight in the total: discomfort is counted, not converted.

**The ledger.** Dead from the cold plus the two life-expectancy channels give **about 1,850 lives** (range 490 to 4,000). Separately, and in a different unit, the attention the war absorbed equals about **1,180 waking lifetimes**. These numbers should not be added to each other, and neither should be compared with the casualties in Ukraine or Iran, which are of a different order.

## Epilogue: who carried it

Every channel in this report bends the same way. The poorest fifth lost 3.7% of its income before support against 1.3% for the richest. It was nearly five times as likely to take no holiday (38% against 8%) and twice as likely to worry about money (about 40% against 20%). The households that fell through the support scheme were, by construction, in the bottom fifth. When support was generous, energy poverty fell during the worst price shock in fifty years; when it ended, energy poverty returned to 6%.

"Injustice anywhere is a threat to justice everywhere," Martin Luther King Jr. wrote in 1963. The Dutch data are a small, measurable instance of the idea: a war in one place produced its injuries here along the existing lines of inequality. Nelson Mandela's version, from Trafalgar Square in 2005, is closer to a policy conclusion: "As long as poverty, injustice and gross inequality persist in our world, none of us can truly rest."

## How much the answer depends on our choices

| Choice | Poorest fifth, net % of income | Richest fifth, net % of income |
|---|---|---|
| Central case | −1.85 | 1.08 |
| Published energy prices (new contracts only) | −2.74 | 0.82 |
| CBS recomputed energy prices | −0.96 | 1.32 |
| 2015 instead of 2020 spending pattern | −1.95 | 1.00 |
| Each category's own 24-month pre-war trend | −3.71 | 0.46 |
| Add excess core inflation | 3.33 | 2.88 |

Negative means the fifth came out ahead.

The energy series matters most. Before June 2023, Dutch energy prices were measured from new contracts only. CBS later recomputed the series with existing contracts. The recomputed CPI ran up to 8.1 index points below the published one in September 2022, and above it from January 2023. Anchored at February 2022, the published series undercounts what households on fixed contracts paid in 2023. The recomputed series counts the delayed pass-through of the autumn-2021 gas spike, which happened before the invasion. Each is biased, in opposite directions, so the central case takes the midpoint. The recomputation was published only as total CPI levels, so the correction is applied to the energy channel in proportion to each fifth's energy share.

The pre-trend counterfactual looks like the more data-driven option and is the worse one. Energy prices rose steeply between February 2020 and February 2022, so extrapolating that trend says the war *lowered* energy costs. The 2015 survey changes almost nothing. Including core inflation changes everything, which is exactly why it stays out of the headline.

## Limitations

The spending weights are from 2020, a lockdown year. Swapping in 2015 moves the results by about 0.1 percentage points, but neither year reflects how households cut gas use by about a quarter in 2022 (CBS via NOS, 2023). That makes our cash losses an upper bound, since we price the pre-crisis basket.

Quintile averages hide everything inside the quintile. A renter in a poorly insulated flat on a variable contract and a homeowner with solar panels can share a fifth. The budget survey is the only source that links spending to income, and CBS publishes it by fifth, not by household.

Income is registered disposable income, and pensions, wages and benefits were partly indexed to 2022–23 inflation. Indexation is a delayed form of compensation that this model leaves out, so the net losses are overstated for wage earners whose collective agreements caught up [citation needed].

The CBS research series was transcribed from a CBS article, not downloaded from StatLine. It was checked against the inflation rates printed alongside it, but should be re-verified before anyone cites a single month.

## Disclaimer and AI assistance

This is an independent, non-commercial analysis. It is not affiliated with, endorsed by or produced on behalf of Statistics Netherlands (CBS), Eurostat, the CPB, any ministry, news organisation or other source cited here; names are used only to identify sources. The casualty figures are model estimates built from published data and stated assumptions. They are not official statistics, not a count of identified deaths or injuries, and do not describe any individual; quote them only with their ranges. Nothing here is medical, financial, legal or policy advice. The material is provided "as is", without warranty of any kind, and to the fullest extent permitted by law the authors accept no liability for any loss arising from its use. CBS and Eurostat data are reused under CC BY 4.0; other sources remain the property of their owners, and short quotations are used for commentary.

**AI assistance.** This project was made with the help of Claude, an AI model developed by Anthropic, which assisted with research, data analysis, code, charts and writing. Figures were checked against the cited sources, but errors are possible; please report them through the issue tracker.

## References

- CBS (2022). Uitwerking van energiemaatregelen in de CPI. https://www.cbs.nl/nl-nl/achtergrond/2022/48/uitwerking-van-energiemaatregelen-in-de-cpi
- CBS (2022). Rijkste Nederlanders kwarteeuw langer gezond dan armste (reported by ANP, 21 December 2022).
- CBS (2023). CBS stapt over op nieuwe methode voor energieprijzen in de CPI. https://www.cbs.nl/nl-nl/achtergrond/2023/26/cbs-stapt-over-op-nieuwe-methode-voor-energieprijzen-in-de-cpi
- CBS (2026). Afname energiearmoede stagneert in 2025. https://www.cbs.nl/nl-nl/nieuws/2026/30/afname-energiearmoede-stagneert-in-2025
- CBS StatLine tables 85420NED, 85419NED, 83932NED (CC BY 4.0).
- Eurostat. HICP, ECOICOP version 2, monthly data (`prc_hicp_minr`).
- SZW (2024, 10 June). Beslisnota bij Monitor uitvoering energietoeslag, meting 2 (Bureau Bartels). https://berthub.eu/tkconv/getraw/2024D26690
- NL Times (2026, 31 March). High energy & fuel prices push Dutch inflation to 2.7% in March. https://nltimes.nl/node/87720
- CBS via NOS (2023, 13 February). Korter douchen en verwarming uit: laagste gasverbruik in 50 jaar. https://nos.nl/l/2463617
- CBS via ANP (2022, 9 December). CBS: afgelopen maand 10 procent meer sterfgevallen dan verwacht. https://nieuws.nl/algemeen/cbs-afgelopen-maand-10-procent-meer-sterfgevallen-dan-verwacht
- CBS via ANP (2023, 25 January). Nog steeds veel oversterfte in 2022, vooral door griep en covid. https://nieuws.nl/algemeen/nog-steeds-veel-oversterfte-in-2022-vooral-door-griep-en-covid
- CBS (2022). Consumentenvertrouwen verandert niet. https://www.cbs.nl/nl-nl/nieuws/2022/42/consumentenvertrouwen-verandert-niet
- CBS (2026). Consumentenvertrouwen daalt verder in mei. https://www.cbs.nl/nl-nl/nieuws/2026/21/consumentenvertrouwen-daalt-verder-in-mei
- CBS (2024). 1 op de 5 Nederlanders ging in 2023 niet op vakantie. https://www.cbs.nl/nl-nl/nieuws/2024/28/1-op-de-5-nederlanders-ging-in-2023-niet-op-vakantie
- CBS via ANP (2023, 8 June). Steeds meer Nederlanders maken zich zorgen over hun financiële situatie. https://www.hartvannederland.nl/algemeen-nieuws/artikelen/steeds-meer-nederlanders-maken-zich-zorgen-over-hun-financiele-situatie
- I&O Research for NOS (2022, 8 March), via Binnenlands Bestuur. Nederlanders maken zich grote zorgen om oorlog Oekraïne. https://www.binnenlandsbestuur.nl/bestuur-en-organisatie/io-research/nederlanders-maken-zich-grote-zorgen-om-oorlog-oekraine
- NCTV (2022, 14 March). Flitspeiling Oekraïne 2.
- Nibud via NL Times (2022, 15 September). Netherlands heading for debt crisis, budget institute warns. https://nltimes.nl/2022/09/15/netherlands-heading-debt-crisis-budget-institute-warns
- NL Times (2026, 16 April). KLM scraps 160 flights in key holiday amid soaring fuel prices. https://nltimes.nl/2026/04/16/klm-scraps-160-flights-key-holiday-amid-soaring-fuel-prices-middle-east-tension
- Tweede Kamer (2022). Kamervoorzitter: '2022 was jaar van grote gebeurtenissen en emoties'. https://www.tweedekamer.nl/nieuws/kamernieuws/kamervoorzitter-2022-was-jaar-van-grote-gebeurtenissen-en-emoties
- TV Gids (2022, 8 March). Kijkcijfers: Giro555, Oekraïne-journaals. https://www.tvgids.nl/nieuws/televisie/de-tv-van-gisteren-kijkcijfers-giro555-oekraine-journaals-hunted-into-the-wild
- Voedselbanken Nederland via NOS (2026, 2 June). Na daling nu weer meer mensen naar voedselbank. https://nos.nl/l/2616784
- Wynia's Week (2023, 1 April). Nederlandse huizen zijn een stuk killer geworden (Milieu Centraal, tado). https://www.wyniasweek.nl/nederlandse-huizen-zijn-een-stuk-killer-geworden/
- CPB via NOS (2026, 16 April). CPB: huishoudens gaan erop achteruit door oorlog Midden-Oosten. https://nos.nl/l/2610684
- Chirakijja, J., Jayachandran, S. and Ong, P. (2023). The mortality effects of winter heating prices. *Economic Journal* 134(657), 402–417. https://pmc.ncbi.nlm.nih.gov/articles/PMC10702363/
- CBS (2023). Eind januari geen oversterfte meer. https://www.cbs.nl/nl-nl/nieuws/2023/05/eind-januari-geen-oversterfte-meer
- The Economist (2023, 10 May), via American Experiment. https://www.americanexperiment.org/the-economist-higher-energy-prices-may-have-killed-more-europeans-last-winter-than-covid-19/
- ScotPHO. Scottish Burden of Disease: anxiety (GBD disability weights). https://www.scotpho.org.uk/media/1778/sbod2016-anxiety2.pdf
- Voedselbanken Nederland (2023). Feiten en cijfers per 31-12-2022. https://voedselbankennederland.nl/wp-content/uploads/2023/12/Feiten-en-Cijfers-per-31-12-2022-versie-29-12-2023.pdf
- King, M. L. Jr. (1963). Letter from Birmingham Jail.
- Mandela, N. (2005, 3 February). Speech for the Make Poverty History campaign, Trafalgar Square, London.
- Chetty, R. et al. (2016). The association between income and life expectancy in the United States, 2001–2014. *JAMA* 315(16).
- Ruhm, C. J. (2000). Are recessions good for your health? *Quarterly Journal of Economics* 115(2).
