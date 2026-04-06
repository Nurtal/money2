from datetime import date
from unittest.mock import patch

from scrapers.fondation_alzheimer import FondationAlzheimerScraper

BASE = "https://www.fondation-alzheimer.org"
PROG_PATH = "/je-suis-chercheur/financement-de-projets/"

LISTING_HTML = f"""
<html><body>
<main>
  <nav>
    <a href="{BASE}{PROG_PATH}">Appels à projets</a>
  </nav>
  <ul>
    <li><a href="{BASE}{PROG_PATH}allocations-jeunes-chercheurs/">Allocations Jeunes Chercheurs</a></li>
    <li><a href="{BASE}{PROG_PATH}mobilite-internationale-jusqua-12-mois/">Mobilité internationale jusqu'à 12 mois</a></li>
    <li><a href="{BASE}{PROG_PATH}programme-innovant/">Programme Innovant</a></li>
  </ul>
</main>
</body></html>
"""

SUB_HTML_AJC = """
<html><body>
<article>
  <h1>Allocations Jeunes Chercheurs</h1>
  <p>Date limite de soumission : 2 avril 2026, 23:59</p>
  <p>Ce programme finance de jeunes chercheurs en France.</p>
</article>
</body></html>
"""

SUB_HTML_MOBILITE = """
<html><body>
<article>
  <h1>Mobilité internationale</h1>
  <p>Date limite de soumission : 30 septembre 2026, 23:59</p>
  <p>Soutien à la mobilité internationale des chercheurs.</p>
</article>
</body></html>
"""

SUB_HTML_NO_DATE = """
<html><body>
<article>
  <h1>Programme Innovant</h1>
  <p>Ce programme n'a pas encore de date de clôture.</p>
</article>
</body></html>
"""


def make_scraper():
    return FondationAlzheimerScraper()


def test_parse_listing_returns_programme_links():
    s = make_scraper()
    items = s.parse(LISTING_HTML)
    assert len(items) == 3
    assert items[0]["titre"] == "Allocations Jeunes Chercheurs"
    assert items[1]["titre"] == "Mobilité internationale jusqu'à 12 mois"


def test_parse_listing_urls():
    s = make_scraper()
    items = s.parse(LISTING_HTML)
    assert items[0]["url"] == f"{BASE}{PROG_PATH}allocations-jeunes-chercheurs/"
    assert items[1]["url"] == f"{BASE}{PROG_PATH}mobilite-internationale-jusqua-12-mois/"


def test_parse_listing_skips_base_url():
    s = make_scraper()
    items = s.parse(LISTING_HTML)
    assert all(i["url"] != f"{BASE}{PROG_PATH}" for i in items)


def test_fetch_follows_sub_pages():
    s = make_scraper()
    pages = {
        s.base_url: LISTING_HTML,
        f"{BASE}{PROG_PATH}allocations-jeunes-chercheurs/": SUB_HTML_AJC,
        f"{BASE}{PROG_PATH}mobilite-internationale-jusqua-12-mois/": SUB_HTML_MOBILITE,
        f"{BASE}{PROG_PATH}programme-innovant/": SUB_HTML_NO_DATE,
    }
    with patch.object(s, "_get", side_effect=lambda url: pages[url]):
        items = s.fetch()

    assert len(items) == 3
    assert items[0]["titre"] == "Allocations Jeunes Chercheurs"
    assert items[0]["date_raw"] == "2 avril 2026"
    assert items[1]["date_raw"] == "30 septembre 2026"


def test_fetch_no_date_still_returned():
    """Programme with no parseable date is included with empty date_raw."""
    s = make_scraper()
    pages = {
        s.base_url: LISTING_HTML,
        f"{BASE}{PROG_PATH}allocations-jeunes-chercheurs/": SUB_HTML_AJC,
        f"{BASE}{PROG_PATH}mobilite-internationale-jusqua-12-mois/": SUB_HTML_MOBILITE,
        f"{BASE}{PROG_PATH}programme-innovant/": SUB_HTML_NO_DATE,
    }
    with patch.object(s, "_get", side_effect=lambda url: pages[url]):
        items = s.fetch()

    no_date = next(i for i in items if i["titre"] == "Programme Innovant")
    assert no_date["date_raw"] == ""


def test_normalize_with_date():
    s = make_scraper()
    raw = {
        "titre": "Allocations Jeunes Chercheurs",
        "url": f"{BASE}{PROG_PATH}allocations-jeunes-chercheurs/",
        "date_raw": "2 avril 2026",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 4, 2)
    assert result.source == "Fondation Alzheimer"
    assert result.domaine == "neurodégénératif / Alzheimer"
    assert "Alzheimer" in result.mots_cles


def test_normalize_without_date():
    s = make_scraper()
    raw = {
        "titre": "Programme Innovant",
        "url": f"{BASE}{PROG_PATH}programme-innovant/",
        "date_raw": "",
    }
    result = s.normalize(raw)
    assert result.date_limite is None
    assert result.source == "Fondation Alzheimer"
