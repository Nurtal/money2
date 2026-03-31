from datetime import date
from unittest.mock import patch

import pytest

from scrapers.anrs import AnrsScraper

SAMPLE_HTML_P1 = """
<html><body>
<div>
  <div>
    <img src="visuel.jpg" alt="">
    <div>Appel à projets En cours</div>
    <a href="https://anrs.fr/financements/tous-les-appels-a-projets/aap-fellowships-2026/">
      <strong>Appel à candidatures Fellowships 2026</strong>
    </a>
    <p>Dates d'ouverture : 16 février - 25 mars 2026</p>
    <p>Du 16 février 2026 au 25 mars 2026</p>
  </div>
  <div>
    <img src="visuel2.jpg" alt="">
    <div>Appel à projet Terminé</div>
    <a href="https://anrs.fr/financements/tous-les-appels-a-projets/aap-vihsida-2025/">
      <strong>AAP VIH/SIDA 2025</strong>
    </a>
    <p>Du 01 janvier 2025 au 28 février 2025</p>
  </div>
</div>
<a href="https://anrs.fr/financements/tous-les-appels-a-projets/page/2/">2</a>
</body></html>
"""

SAMPLE_HTML_P2 = """
<html><body>
<div>
  <div>
    <div>Appel à projets En cours</div>
    <a href="https://anrs.fr/financements/tous-les-appels-a-projets/aap-hepatites-2026/">
      <strong>AAP Hépatites 2026</strong>
    </a>
    <p>Du 01 mars 2026 au 30 juin 2026</p>
  </div>
</div>
</body></html>
"""


@pytest.fixture
def scraper():
    return AnrsScraper()


def test_parse_extracts_items(scraper):
    items = scraper.parse(SAMPLE_HTML_P1)
    assert len(items) == 2
    assert items[0]["titre"] == "Appel à candidatures Fellowships 2026"
    assert items[0]["url"] == "https://anrs.fr/financements/tous-les-appels-a-projets/aap-fellowships-2026/"


def test_parse_closing_date(scraper):
    items = scraper.parse(SAMPLE_HTML_P1)
    assert items[0]["date_raw"] == "25 mars 2026"
    assert items[1]["date_raw"] == "28 février 2025"


def test_parse_status(scraper):
    items = scraper.parse(SAMPLE_HTML_P1)
    assert items[0]["statut"] == "ouvert"
    assert items[1]["statut"] == "fermé"


def test_normalize(scraper):
    raw = {
        "titre": "Appel à candidatures Fellowships 2026",
        "url": "https://anrs.fr/financements/tous-les-appels-a-projets/aap-fellowships-2026/",
        "date_raw": "25 mars 2026",
        "statut": "ouvert",
    }
    result = scraper.normalize(raw)
    assert result.source == "ANRS"
    assert result.date_limite == date(2026, 3, 25)
    assert result.statut == "ouvert"
    assert "VIH" in result.mots_cles


def test_fetch_paginates(scraper):
    pages = {
        scraper.base_url: SAMPLE_HTML_P1,
        f"{scraper.base_url}page/2/": SAMPLE_HTML_P2,
    }

    def fake_get(url):
        return pages.get(url, "<html><body></body></html>")

    with patch.object(scraper, "_get", side_effect=fake_get):
        items = scraper.fetch()

    assert len(items) == 3


def test_fetch_stops_without_next_page(scraper):
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML_P2

    with patch.object(scraper, "_get", side_effect=fake_get):
        scraper.fetch()

    assert call_count == 1
