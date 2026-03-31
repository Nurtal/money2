from datetime import date
from unittest.mock import patch

import pytest

from scrapers.inca import IncaScraper

SAMPLE_HTML_P1 = """
<html><body>
<ul>
  <li>
    <h3><a href="/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets/seq-rth26">
      AAP Radiothérapie 2026
    </a></h3>
    <p>Cet appel vise à limiter les séquelles de la radiothérapie.</p>
    <p>En cours</p>
    <p>Date limite de soumission : 27 mai 2026 à 16:00</p>
  </li>
  <li>
    <h3><a href="/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets/aap-test-2">
      AAP Prévention Cancer 2025
    </a></h3>
    <p>Prévention et dépistage précoce.</p>
    <p>Clos</p>
    <p>Date limite de soumission : 15/04/2025</p>
  </li>
</ul>
<a href="?page=2">Suivant</a>
</body></html>
"""

SAMPLE_HTML_P2 = """
<html><body>
<ul>
  <li>
    <h3><a href="/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets/aap-test-3">
      AAP Biomarqueurs 2025
    </a></h3>
    <p>Recherche sur les biomarqueurs tumoraux.</p>
    <p>En cours</p>
    <p>Date limite de soumission : 30 septembre 2025</p>
  </li>
</ul>
</body></html>
"""


@pytest.fixture
def scraper():
    return IncaScraper()


def test_parse_extracts_items(scraper):
    items = scraper.parse(SAMPLE_HTML_P1)
    assert len(items) == 2
    assert items[0]["titre"] == "AAP Radiothérapie 2026"
    assert items[0]["date_raw"] == "27 mai 2026"
    assert items[0]["statut"] == "ouvert"
    assert items[1]["statut"] == "fermé"


def test_normalize_french_date(scraper):
    raw = {
        "titre": "AAP Radiothérapie 2026",
        "url": "https://www.cancer.fr/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets/seq-rth26",
        "date_raw": "27 mai 2026",
        "statut": "ouvert",
        "description": "",
    }
    result = scraper.normalize(raw)
    assert result.date_limite == date(2026, 5, 27)
    assert result.source == "INCa"
    assert result.domaine == "oncologie"
    assert "cancer" in result.mots_cles


def test_normalize_slash_date(scraper):
    raw = {
        "titre": "Test",
        "url": "https://www.cancer.fr/test",
        "date_raw": "15/04/2025",
        "statut": "fermé",
        "description": "",
    }
    result = scraper.normalize(raw)
    assert result.date_limite == date(2025, 4, 15)
    assert result.statut == "fermé"


def test_fetch_paginates(scraper):
    pages = {
        scraper.base_url: SAMPLE_HTML_P1,
        f"{scraper.base_url}?page=2": SAMPLE_HTML_P2,
    }

    def fake_get(url):
        return pages.get(url, "<html><body><ul></ul></body></html>")

    with patch.object(scraper, "_get", side_effect=fake_get):
        items = scraper.fetch()

    assert len(items) == 3
    titles = [i["titre"] for i in items]
    assert "AAP Radiothérapie 2026" in titles
    assert "AAP Biomarqueurs 2025" in titles


def test_fetch_stops_without_next_page(scraper):
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML_P2  # no ?page=2 link

    with patch.object(scraper, "_get", side_effect=fake_get):
        scraper.fetch()

    assert call_count == 1
