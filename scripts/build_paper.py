"""Typeset reports/report.md as a working paper PDF with the figures.

Needs two extra packages that the pipeline itself does not:
    pip install markdown playwright && playwright install chromium
Run from the repository root:
    python scripts/build_paper.py
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "report.md"
OUT = ROOT / "reports" / "working_paper.pdf"

# Figure placed after the paragraph that starts with this text.
FIGURES = [
    ("The shock arrived in two waves.", "02_wave_and_ripple", "Excess monthly cost of food, home energy and motor fuel for the average household, months after each war began."),
    ("Over 22 months, food cost", "04_what_drove_it", "Excess monthly cost by category, Russia–Ukraine shock, share of monthly spending."),
    ("Support changes the picture", "01_bleeding_income", "Net war cost after support as a share of disposable income, by income fifth."),
    ("The CBS/TNO energy-poverty monitor", "06_support_while_it_lasted", "Energy poverty 2019–2025 and the poorest fifth's net cost by energietoeslag take-up."),
    ("The result for Ukraine, after support", "05_lifetimes", "Life-years lost to lower income, expressed as full 82-year lifetimes."),
    ("A war shock raises some prices", "03_the_gap_is_the_bill", "Actual prices against the no-war path. The shaded gap is the excess households paid."),
]

CSS = """
@page { size: A4; margin: 22mm 20mm 22mm 20mm; }
:root { --ink: #111214; --ink2: #5a5d63; --rule: #d9dadd; --signal: #dc1c13; }
* { box-sizing: border-box; }
body { font-family: Inter, "Helvetica Neue", Arial, sans-serif; font-size: 9.6pt; line-height: 1.5; color: var(--ink); margin: 0; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: space-between; page-break-after: always; }
.cover .top { border-top: 3px solid var(--ink); padding-top: 4mm; display: flex; justify-content: space-between;
  font-family: "DejaVu Sans Mono", monospace; font-size: 7.5pt; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink2); }
.cover h1 { font-size: 46pt; font-weight: 900; line-height: 0.95; letter-spacing: -0.03em; margin: 0 0 6mm; }
.cover h1 span { color: var(--signal); }
.cover .sub { font-size: 15pt; font-weight: 500; max-width: 130mm; line-height: 1.3; }
.cover .keys { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 2px solid var(--ink); }
.cover .keys div { padding: 3mm 3mm 0 0; }
.cover .keys div + div { border-left: 1px solid var(--rule); padding-left: 3mm; }
.cover .keys b { display: block; font-size: 20pt; font-weight: 800; letter-spacing: -0.02em; }
.cover .keys span { font-size: 7.5pt; color: var(--ink2); line-height: 1.3; display: block; }
.cover .foot { font-family: "DejaVu Sans Mono", monospace; font-size: 7pt; color: var(--ink2); border-top: 1px solid var(--rule); padding-top: 3mm; }
.summary { page-break-after: always; }
.summary h2 { margin-top: 0; }
.summary ol { padding-left: 5mm; display: grid; gap: 2.5mm; }
h1.title { display: none; }
h2 { font-size: 15pt; font-weight: 800; letter-spacing: -0.01em; margin: 9mm 0 3mm; border-top: 2px solid var(--ink); padding-top: 2.5mm; break-after: avoid; }
p { margin: 0 0 2.8mm; orphans: 3; widows: 3; }
strong { font-weight: 700; }
em { font-style: italic; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; }
table { width: 100%; border-collapse: collapse; margin: 3mm 0 4mm; font-size: 8.6pt; break-inside: avoid; }
th { text-align: left; border-bottom: 1.5px solid var(--ink); padding: 1.5mm 2mm 1.5mm 0; font-weight: 700; }
td { border-bottom: 1px solid var(--rule); padding: 1.5mm 2mm 1.5mm 0; }
td:not(:first-child), th:not(:first-child) { text-align: right; font-variant-numeric: tabular-nums; }
figure { margin: 4mm 0 5mm; break-inside: avoid; }
figure img { width: 100%; display: block; }
figcaption { font-size: 7.8pt; color: var(--ink2); margin-top: 1.5mm; border-top: 1px solid var(--rule); padding-top: 1.5mm; }
ul { padding-left: 4mm; }
li { margin-bottom: 1.2mm; }
.refs li { font-size: 7.8pt; word-break: break-word; }
.appendix { page-break-before: always; }
"""


def img_tag(name: str) -> str:
    data = base64.b64encode((ROOT / "figures" / f"{name}.png").read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" alt="">'


def body_html() -> str:
    text = REPORT.read_text(encoding="utf-8")
    text = re.sub(r"^A companion story page.*\n", "", text, flags=re.M)
    html = markdown.markdown(text, extensions=["tables"])
    # Number figures in reading order and point the text's "(figure N)" references,
    # which use the file numbers, at the new numbers.
    placed = sorted(FIGURES, key=lambda f: html.index("<p>" + f[0]))
    number_of = {int(fig[:2]): k for k, (_, fig, _) in enumerate(placed, start=1)}
    html = re.sub(r"\(figure (\d)\)", lambda m: f"(figure {number_of[int(m.group(1))]})", html)
    for k, (start, fig, caption) in enumerate(placed, start=1):
        pattern = re.compile(r"(<p>" + re.escape(start) + r".*?</p>)", re.S)
        html, n = pattern.subn(
            lambda m: m.group(1) + f"<figure>{img_tag(fig)}<figcaption>Figure {k}. {caption}</figcaption></figure>",
            html, count=1)
        if not n:
            raise ValueError(f"anchor paragraph not found: {start}")
    html = html.replace("<h2>References</h2>\n<ul>", '<h2>References</h2>\n<ul class="refs">')
    return html.replace("<h1>", '<h1 class="title">', 1)


def appendix_html() -> str:
    review = (ROOT / "reports" / "review.md").read_text(encoding="utf-8")
    review = review.replace("# Referee report on version 0.1", "## Appendix: referee notes on this project")
    # The figure design notes are for the repository, not the paper.
    sections = re.split(r"(?m)^(?=## )", review)
    review = "".join(part for part in sections if not part.startswith("## Figure design notes"))
    return '<section class="appendix">' + markdown.markdown(review, extensions=["tables"]) + "</section>"


def cover_html(numbers: dict) -> str:
    u, i = numbers["ukraine"], numbers["iran"]
    household = sum(u["gross_eur"].values()) / 5
    days = u["days_per_person_central_net"]
    return f"""
<section class="cover">
  <div class="top"><span>Working paper No. 1</span><span>October 2026 · prices to {numbers['latest_price_month']}</span></div>
  <div>
    <h1>Hidden<br>casualties<span>.</span></h1>
    <p class="sub">What the Russia–Ukraine and Iran war price shocks cost Dutch households in money, warmth, attention and life expectancy.</p>
  </div>
  <div class="keys">
    <div><b>€{household:,.0f}</b><span>extra spent per household on food, energy and fuel, Mar 2022 – Dec 2023</span></div>
    <div><b>€{u['national_gross_eur_bn']:.1f} bn</b><span>national excess cost, of which support returned €{u['national_compensation_eur_bn']:.1f} bn</span></div>
    <div><b>{days * 24:.1f} h</b><span>life expectancy lost per resident, central estimate ({u['lifetimes']['central_net']:.0f} lifetimes)</span></div>
    <div><b>€{sum(i['gross_eur'].values()) / 5:,.0f}</b><span>Iran war cost per household so far</span></div>
  </div>
  <div class="foot">war-casualties-nl · github.com/akramvanahmed-projects/war-casualties-nl · Data: CBS and Eurostat (CC BY 4.0). Model estimates, not official statistics.</div>
</section>
<section class="summary">
  <h2>Key findings</h2>
  <ol>
    <li><strong>Food, not energy, was the lasting cost.</strong> Energy prices peaked 96% above their no-war path in October 2022 and fell below it under the 2023 price ceiling. Food never came back down: still 14% above its path at the end of 2023, €1,073 per household in total.</li>
    <li><strong>The official inflation figure mistimed the shock.</strong> In September 2022 published inflation was 14.5%; recomputed with the contracts households actually held, it was 7.8%. By January 2023 the order had reversed: 7.6% published, 11.6% paid.</li>
    <li><strong>Support rescued the poorest fifth and left the middle exposed.</strong> After support the poorest fifth came out 1.9% of income ahead on average (break-even at 32% take-up of the energietoeslag; municipalities report 86–90% reach). The middle three fifths lost 1.5–1.7% of income.</li>
    <li><strong>"The poor lost most" is a denominator effect.</strong> As a share of spending, every fifth lost 2.7–3.1%. The regressive pattern in income terms comes from the poorest fifth spending 1.34 times its registered income.</li>
    <li><strong>The health toll is small and uncertain; the attention toll is large and assumed.</strong> Via the income–longevity gradient, about {u['lifetimes']['central_net']:.0f} lifetimes (range {u['lifetimes']['low_net']:.0f}–{u['lifetimes']['high_net']:.0f}), or {days * 24:.1f} hours per resident. Time spent following and worrying about the war adds up to roughly 1,200 waking lifetimes under stated assumptions.</li>
    <li><strong>Iran is landing on an uncushioned country.</strong> €{sum(i['gross_eur'].values()) / 5:,.0f} per household so far, almost all motor fuel. Energy poverty is back at 6%, higher than at any point during the Ukraine shock, and no support package comparable to 2022 is in place.</li>
  </ol>
</section>
"""


def build() -> None:
    numbers = json.loads((ROOT / "reports" / "key_numbers.json").read_text())
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>" \
           f"{cover_html(numbers)}{body_html()}{appendix_html()}</body></html>"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        footer = ("<div style='width:100%;font-family:DejaVu Sans Mono,monospace;font-size:7px;color:#5a5d63;"
                  "padding:0 20mm;display:flex;justify-content:space-between'><span>Hidden casualties · Working paper No. 1"
                  "</span><span><span class='pageNumber'></span> / <span class='totalPages'></span></span></div>")
        page.pdf(path=str(OUT), format="A4", print_background=True, display_header_footer=True,
                 header_template="<div></div>", footer_template=footer,
                 margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"})
        browser.close()


if __name__ == "__main__":
    build()
