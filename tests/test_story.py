import json

import pytest

from warcost.config import PROCESSED, ROOT
from warcost.story import story_data

pytestmark = pytest.mark.skipif(not (PROCESSED / "summary_ukraine.csv").exists(),
                                reason="needs committed processed data")


def test_story_numbers_match_key_numbers(cfg):
    data = story_data(cfg)
    numbers = json.loads((ROOT / "reports" / "key_numbers.json").read_text())
    assert data["ukraine"]["lifetimes"]["central_net"] == round(numbers["ukraine"]["lifetimes"]["central_net"])
    assert data["ukraine"]["nationalGrossBn"] == round(numbers["ukraine"]["national_gross_eur_bn"], 1)
    assert len(data["ukraine"]["netPct"]) == 5
    json.dumps(data)


def test_phantom_series_reproduces_cbs_september_2022(cfg):
    september = next(p for p in story_data(cfg)["phantom"] if p["m"] == "2022-09")
    assert september["published"] == pytest.approx(14.5, abs=0.1)
    assert september["actual"] == pytest.approx(7.8, abs=0.1)


def test_template_has_data_placeholder():
    assert "/*__DATA__*/null" in (ROOT / "docs" / "story_template.html").read_text()
