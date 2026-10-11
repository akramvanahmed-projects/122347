# Are there human casualties in the Netherlands from the wars in Ukraine and Iran?

**Read the story:** [interactive data story](https://htmlpreview.github.io/?https://github.com/akramvanahmed-projects/war-casualties-nl/blob/main/docs/index.html) · **Working paper:** [PDF](reports/working_paper.pdf) · **Explore the model:** [live dashboard](https://122347-f4egxbgtuuazk7ywmu563y.streamlit.app/)

No bombs fell on the Netherlands, but both wars reached Dutch kitchens and meter cupboards. Between March 2022 and December 2023, the Russia–Ukraine price shock cost the average household about €1,900 in excess spending on food, home energy and motor fuel. That is €15.5 billion nationally. Government support returned €5.9 billion of it, and it did not land evenly.

![Support erased the poorest fifth's war loss. Everyone else still paid.](figures/01_bleeding_income.png)

The poorest fifth lost 3.7% of its income before support and ended up 1.9% ahead after it, assuming 55% of those households claimed the €1,300 energietoeslag in both years. Below 32% take-up they would still have lost. Municipalities estimate they reached about 90% of eligible households in 2022 and 86% in 2023, so the gain is more likely than not, but the share of the poorest fifth that was eligible is not published. Everyone above them paid between 1.1% and 1.7% of income. Measured against spending rather than income, the shock was close to flat: every fifth lost between 2.7% and 3.1% of what it spent. Most of the apparent regressivity comes from the bottom fifth spending a third more than its registered income.

Turned into life expectancy with the Dutch income–longevity gradient, the Ukraine shock cost the equivalent of 113 full 82-year lifetimes after support (plausible range 45 to 226), and support prevented about 72 more. That is 0.19 days per resident. Six months into the Iran war the bill is €78 per household, almost all of it motor fuel, and the life-years equivalent is 3. Household energy prices have not moved yet.

Counted the way an army counts its losses, the Russia–Ukraine shock left the Netherlands with about 1,200 estimated deaths from the cold (range 170–2,200), more than 900,000 people seriously wounded in their finances or health, a light wound on almost everyone, and about 1,850 lives lost once life-expectancy equivalents are added. Money is only part of it. The heating went down two degrees, consumer confidence hit its lowest level since 1986, and the war absorbed attention on a scale that, on stated assumptions, adds up to about 1,200 waking lifetimes, a separate unit from the lives above. The story walks through thirteen chapters in four parts, the bill, the wounded, the dead and the hours, each with its sources and a verdict on how much of it can be blamed on the war.

Figures as of August 2026 prices. The charts and `reports/key_numbers.json` refresh monthly; the prose here does not. The full argument, with every assumption and its weak points, is in [reports/report.md](reports/report.md), and a referee-style critique of the project is in [reports/review.md](reports/review.md).

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
