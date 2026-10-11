# Are there human casualties in the Netherlands from the wars in Ukraine and Iran?

**Read the story:** [interactive data story](https://htmlpreview.github.io/?https://github.com/akramvanahmed-projects/war-casualties-nl/blob/main/docs/index.html) · **Working paper:** [PDF](reports/working_paper.pdf) · **Live app (story and model explorer):** [Streamlit](https://122347-f4egxbgtuuazk7ywmu563y.streamlit.app/)

No bombs fell on the Netherlands, but both wars reached Dutch kitchens and meter cupboards. **Every number here covers one period: March 2022 to August 2026**, from the invasion of Ukraine to the latest month with price data, for both wars. Over that period the Russia–Ukraine price shock cost the average household about €4,270 in excess spending on food, home energy and motor fuel. That is €35.2 billion nationally. Government support, paid only in 2022 and 2023, returned €5.9 billion of it, and it did not land evenly.

![Support carried the poorest fifth while it lasted. Over the whole period, every fifth paid.](figures/01_bleeding_income.png)

In the support years (March 2022 to December 2023) the poorest fifth came out 1.9% of income ahead, assuming 55% of those households claimed the €1,300 energietoeslag in both years; below 32% take-up they would still have lost. Then support ended and the war's price level stayed. Over the whole period the poorest fifth lost 1.1% of its income after support, the middle three fifths 1.5–1.8% and the richest 1.0%. Measured against spending rather than income, the shock was close to flat: every fifth lost between 2.5% and 2.7% of what it spent. Most of the apparent regressivity comes from the bottom fifth spending a third more than its registered income.

Turned into life expectancy with the Dutch income–longevity gradient, the Ukraine shock cost the equivalent of 306 full 82-year lifetimes after support (plausible range 123 to 613), and support prevented about 85 more. That is about 12.6 hours per resident. Six months into the Iran war the bill is €78 per household, almost all of it motor fuel, and the life-years equivalent is 3. Household energy prices have not moved yet.

Counted the way an army counts its losses, over the same period the two wars left the Netherlands with about 2,100 estimated deaths from the cold over four winters (range 300–3,800; about 1,200 of them in the first winter), more than 900,000 people seriously wounded in their finances or health, a light wound on almost everyone, and about 3,050 lives lost once life-expectancy equivalents are added (range 750–6,400). Money is only part of it. The heating went down two degrees, consumer confidence hit its lowest level since 1986, and the wars absorbed attention on a scale that, on stated assumptions, adds up to about 2,280 waking lifetimes, a separate unit from the lives above. The story walks through thirteen chapters in four parts, the bill, the wounded, the dead and the hours, each with its sources and a verdict on how much of it can be blamed on the war.

Figures as of August 2026 prices; the end of the period moves forward each month. After December 2023 the war's price level is held at its late-2023 excess and no later inflation is attributed to it. The charts and `reports/key_numbers.json` refresh monthly; the prose here does not. The full argument, with every assumption and its weak points, is in [reports/report.md](reports/report.md), and a referee-style critique of the project is in [reports/review.md](reports/review.md).

## How to reproduce

```bash
git clone https://github.com/akramvanahmed-projects/war-casualties-nl.git && cd war-casualties-nl
pip install -r requirements.txt
python -m warcost all          # fetch, analyse, draw figures, build the story page
streamlit run app.py           # interactive version
```

The working paper PDF is typeset with `python scripts/build_paper.py`, which needs `markdown` and `playwright` on top of the requirements.

`fetch` downloads Eurostat and CBS tables (about 10 MB, cached in `data/raw/`). `analyse` writes per-quintile summaries and a sensitivity grid to `data/processed/`, and the numbers quoted above to `reports/key_numbers.json`. The processed data is committed, so `analyse`, `figures` and the app also work offline. `pytest` runs the model checks against synthetic inputs with known answers. A GitHub Action refreshes the data on the 3rd of every month.

## Layout

```
config.yaml              every source pointer and assumption, with ranges
src/warcost/             sources, prices, exposure, health, analysis, figures
data/external/           CBS energy-method series; sourced facts for the story
data/processed/          model inputs and outputs (committed)
figures/                 PNG (300 dpi) and SVG
docs/                    story page (index.html, built from story_template.html)
reports/                 report.md, review.md, working_paper.pdf, key_numbers.json
notebooks/               walkthrough.ipynb
app.py                   Streamlit dashboard
tests/                   pytest
```

## Data and licence

Code is MIT-licensed (see `LICENSE`). Data comes from Eurostat (HICP, `prc_hicp_minr`) and Statistics Netherlands (StatLine tables 85420NED, 85419NED and 83932NED, plus published figures on energy poverty and life expectancy), all reused under CC BY 4.0. Source: CBS and Eurostat. The results are this project's own modelling, not official statistics.

## Disclaimer

This is an independent, non-commercial analysis. It is not affiliated with, endorsed by or produced on behalf of Statistics Netherlands (CBS), Eurostat, the CPB, any ministry, news organisation or other source cited here; names are used only to identify sources. The casualty figures are model estimates built from published data and stated assumptions. They are not official statistics, not a count of identified deaths or injuries, and do not describe any individual; quote them only with their ranges. Nothing here is medical, financial, legal or policy advice. The material is provided "as is", without warranty of any kind, and to the fullest extent permitted by law the authors accept no liability for any loss arising from its use. CBS and Eurostat data are reused under CC BY 4.0; other sources remain the property of their owners, and short quotations are used for commentary.

**AI assistance.** This project was made with the help of Claude, an AI model developed by Anthropic, which assisted with research, data analysis, code, charts and writing. Figures were checked against the cited sources, but errors are possible; please report them through the issue tracker.
