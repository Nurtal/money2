from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from scrapers.anr import AnrScraper

SAMPLE_HTML = """
<html><body>
<div class="tx-solr-results-item">
  <h3 class="tx-solr-results-title">
    <a href="/fr/detail/call/aap-test-2025/">AAP Santé Numérique 2025</a>
  </h3>
  <p class="tx-solr-results-type">Appel à projets générique</p>
  <p class="tx-solr-results-dates">01/01/2025 - 30/06/2025</p>
  <p class="tx-solr-results-description">Ouvert aux équipes de recherche publique.</p>
  <a href="/fr/detail/call/aap-test-2025/">Plus de détails</a>
</div>
<div class="tx-solr-results-item">
  <h3 class="tx-solr-results-title">
    <a href="/fr/detail/call/aap-cancer-2025/">AAP Cancer et Innovation</a>
  </h3>
  <p class="tx-solr-results-type">Appel à projets spécifique</p>
  <p class="tx-solr-results-dates">15/02/2025 - 15/09/2025</p>
  <p class="tx-solr-results-description">Financement de projets en oncologie.</p>
  <a href="/fr/detail/call/aap-cancer-2025/">Plus de détails</a>
</div>
<ul class="pagination">
  <li><a href="/fr/appels-ouverts/">1</a></li>
</ul>
</body></html>
"""


@pytest.fixture
def scraper():
    return AnrScraper()


def test_fetch_parses_items(scraper):
    with patch.object(scraper, "_get", return_value=SAMPLE_HTML):
        items = scraper.fetch()
    assert len(items) == 2
    assert items[0]["titre"] == "AAP Santé Numérique 2025"
    assert items[0]["url"] == "https://anr.fr/fr/detail/call/aap-test-2025/"
    assert items[0]["dates_raw"] == "01/01/2025 - 30/06/2025"


def test_normalize_extracts_closing_date(scraper):
    raw = {
        "titre": "AAP Santé Numérique 2025",
        "url": "https://anr.fr/fr/detail/call/aap-test-2025/",
        "dates_raw": "01/01/2025 - 30/06/2025",
        "description": "Ouvert aux équipes de recherche publique.",
        "type": "Appel à projets générique",
    }
    result = scraper.normalize(raw)
    assert result.titre == "AAP Santé Numérique 2025"
    assert result.source == "ANR"
    assert result.date_limite == date(2025, 6, 30)
    assert result.url_source == "https://anr.fr/fr/detail/call/aap-test-2025/"


def test_normalize_keywords(scraper):
    raw = {
        "titre": "AAP Cancer et Innovation numérique",
        "url": "https://anr.fr/fr/detail/call/aap-cancer/",
        "dates_raw": "01/01/2025 - 30/06/2025",
        "description": "",
        "type": "",
    }
    result = scraper.normalize(raw)
    assert "cancer" in result.mots_cles
    assert "innovation" in result.mots_cles
    assert "numérique" in result.mots_cles


def test_normalize_single_date(scraper):
    raw = {
        "titre": "Test",
        "url": "https://anr.fr/fr/detail/call/test/",
        "dates_raw": "30/06/2025",
        "description": "",
        "type": "",
    }
    result = scraper.normalize(raw)
    assert result.date_limite == date(2025, 6, 30)


def test_normalize_missing_date(scraper):
    raw = {
        "titre": "Test",
        "url": "https://anr.fr/fr/detail/call/test/",
        "dates_raw": "",
        "description": "",
        "type": "",
    }
    result = scraper.normalize(raw)
    assert result.date_limite is None


def test_pagination_stops_without_next(scraper):
    """Scraper should stop after page 0 when there is no page=1 link."""
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML  # no tx_solr[page]=1 link in pagination

    with patch.object(scraper, "_get", side_effect=fake_get):
        items = scraper.fetch()

    assert call_count == 1
    assert len(items) == 2
