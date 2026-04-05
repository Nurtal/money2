from datetime import date
from unittest.mock import patch

from scrapers.anr import AnrScraper

# HTML matching the real ANR structure (div.card.appel / h2 a / div.date / span.tag-type)
SAMPLE_HTML = """
<html><body>
<div class="card appel col-12 col-md-6">
  <div class="card-header pb-0">
    <div class="categories">
      <span class="tag-type">Appel à projets spécifique</span>
    </div>
    <div class="date">02/04/2026
        - 04/06/2026</div>
  </div>
  <div class="card-body">
    <div class="main_content">
      <h2><a href="/fr/detail/call/aap-test-2026/">AAP Santé Numérique 2026</a></h2>
    </div>
    <div class="abstract"><p>Ouvert aux équipes de recherche publique.</p></div>
  </div>
</div>
<div class="card appel col-12 col-md-6">
  <div class="card-header pb-0">
    <div class="categories">
      <span class="tag-type">Appel à projets spécifique</span>
    </div>
    <div class="date">Avril 2026
        - Juin 2026</div>
  </div>
  <div class="card-body">
    <div class="main_content">
      <h2><a href="/fr/detail/call/aap-cancer-2026/">AAP Cancer et Innovation</a></h2>
    </div>
    <div class="abstract"><p>Financement de projets en oncologie.</p></div>
  </div>
</div>
<ul class="pagination">
  <li class="page-item active"><span class="page-link">1</span></li>
</ul>
</body></html>
"""

SAMPLE_HTML_P2 = """
<html><body>
<div class="card appel col-12 col-md-6">
  <div class="card-header pb-0">
    <div class="date">01/09/2026 - 30/11/2026</div>
  </div>
  <div class="card-body">
    <div class="main_content">
      <h2><a href="/fr/detail/call/aap-p2/">AAP Page 2</a></h2>
    </div>
    <div class="abstract"><p>Description page 2.</p></div>
  </div>
</div>
<ul class="pagination">
  <li class="page-item active"><span class="page-link">2</span></li>
</ul>
</body></html>
"""


def make_scraper():
    return AnrScraper()


def test_fetch_parses_items():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    assert len(items) == 2
    assert items[0]["titre"] == "AAP Santé Numérique 2026"
    assert items[0]["url"] == "https://anr.fr/fr/detail/call/aap-test-2026/"


def test_fetch_date_raw_slash_format():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    # Whitespace collapsed; " - " separator preserved
    assert "02/04/2026" in items[0]["date_raw"]
    assert "04/06/2026" in items[0]["date_raw"]


def test_fetch_date_raw_month_format():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    assert "Avril 2026" in items[1]["date_raw"]
    assert "Juin 2026" in items[1]["date_raw"]


def test_normalize_closing_date_slash():
    s = make_scraper()
    raw = {
        "titre": "AAP Santé Numérique 2026",
        "url": "https://anr.fr/fr/detail/call/aap-test-2026/",
        "date_raw": "02/04/2026 - 04/06/2026",
        "description": "",
        "type": "",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 6, 4)


def test_normalize_closing_date_month():
    s = make_scraper()
    raw = {
        "titre": "AAP Cancer et Innovation",
        "url": "https://anr.fr/fr/detail/call/aap-cancer-2026/",
        "date_raw": "Avril 2026 - Juin 2026",
        "description": "",
        "type": "",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 6, 1)


def test_normalize_missing_date():
    s = make_scraper()
    raw = {
        "titre": "Test",
        "url": "https://anr.fr/fr/detail/call/test/",
        "date_raw": "",
        "description": "",
        "type": "",
    }
    assert s.normalize(raw).date_limite is None


def test_normalize_keywords():
    s = make_scraper()
    raw = {
        "titre": "AAP Cancer et Innovation numérique",
        "url": "https://anr.fr/fr/detail/call/aap-cancer/",
        "date_raw": "",
        "description": "",
        "type": "",
    }
    result = s.normalize(raw)
    assert "cancer" in result.mots_cles
    assert "innovation" in result.mots_cles
    assert "numérique" in result.mots_cles


def test_normalize_source_and_domain():
    s = make_scraper()
    raw = {
        "titre": "Test",
        "url": "https://anr.fr/fr/detail/call/test/",
        "date_raw": "",
        "description": "",
        "type": "",
    }
    result = s.normalize(raw)
    assert result.source == "ANR"
    assert result.domaine == "recherche"


def test_pagination_stops_without_next():
    """Scraper should stop after page 0 when there is no page=1 link."""
    s = make_scraper()
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML  # no tx_solr[page]=1 link

    with patch.object(s, "_get", side_effect=fake_get):
        items = s.fetch()

    assert call_count == 1
    assert len(items) == 2


def test_pagination_follows_next_page():
    """Scraper fetches page 2 when pagination link exists."""
    s = make_scraper()

    html_p1 = SAMPLE_HTML.replace(
        '<ul class="pagination">',
        '<ul class="pagination"><li><a class="page-link" href="/fr/appels/?tx_solr%5Bpage%5D=1">2</a></li>',
    )
    pages = {s.base_url: html_p1, f"{s.base_url}?tx_solr%5Bpage%5D=1": SAMPLE_HTML_P2}

    with patch.object(s, "_get", side_effect=lambda url: pages[url]):
        items = s.fetch()

    assert len(items) == 3
