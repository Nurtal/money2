from datetime import date
from unittest.mock import patch

from scrapers.anrs import AnrsScraper

# HTML matching the real ANRS structure (div.card-free / h2 a / .card-free__footer p)
SAMPLE_HTML_P1 = """
<html><body>
<ul>
  <li>
    <div class="card-free card-free--result-square position-relative" data-card-link="">
      <div class="card-free__inner">
        <div class="card-free__tags">
          <span class="tag tag--dark"><span>Appel à projet</span></span>
          <span class="tag tag--primary"><span>En cours</span></span>
        </div>
        <h2 class="card-free__title mt-0 mb-2">
          <a href="https://anrs.fr/financements/tous-les-appels-a-projets/aap-fellowships-2026/">
            Appel à candidatures Fellowships 2026
          </a>
        </h2>
        <p class="card-free__excerpt mb-0">Dates d'ouverture : 16 février - 25 mars 2026</p>
        <div class="card-free__footer">
          <p class="m-0">Du 16 février 2026 au 25 mars 2026</p>
        </div>
      </div>
    </div>
  </li>
  <li>
    <div class="card-free card-free--result-square position-relative" data-card-link="">
      <div class="card-free__inner">
        <div class="card-free__tags">
          <span class="tag tag--dark"><span>Appel à projet</span></span>
          <span class="tag tag--primary"><span>Terminé</span></span>
        </div>
        <h2 class="card-free__title mt-0 mb-2">
          <a href="https://anrs.fr/financements/tous-les-appels-a-projets/aap-vih-2025/">
            AAP VIH/SIDA 2025
          </a>
        </h2>
        <div class="card-free__footer">
          <p class="m-0">Du 01 janvier 2025 au 28 février 2025</p>
        </div>
      </div>
    </div>
  </li>
</ul>
<a href="https://anrs.fr/financements/tous-les-appels-a-projets/page/2/">2</a>
</body></html>
"""

SAMPLE_HTML_P2 = """
<html><body>
<ul>
  <li>
    <div class="card-free card-free--result-square position-relative" data-card-link="">
      <div class="card-free__inner">
        <div class="card-free__tags">
          <span class="tag tag--primary"><span>En cours</span></span>
        </div>
        <h2 class="card-free__title mt-0 mb-2">
          <a href="https://anrs.fr/financements/tous-les-appels-a-projets/aap-hepatites-2026/">
            AAP Hépatites 2026
          </a>
        </h2>
        <div class="card-free__footer">
          <p class="m-0">Du 01 mars 2026 au 30 juin 2026</p>
        </div>
      </div>
    </div>
  </li>
</ul>
</body></html>
"""


def make_scraper():
    return AnrsScraper()


def test_parse_extracts_items():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert len(items) == 2
    assert items[0]["titre"] == "Appel à candidatures Fellowships 2026"
    assert items[0]["url"] == "https://anrs.fr/financements/tous-les-appels-a-projets/aap-fellowships-2026/"


def test_parse_closing_date():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert items[0]["date_raw"] == "25 mars 2026"
    assert items[1]["date_raw"] == "28 février 2025"


def test_parse_status_open():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert items[0]["statut"] == "ouvert"


def test_parse_status_closed():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert items[1]["statut"] == "fermé"


def test_normalize():
    s = make_scraper()
    raw = {
        "titre": "Appel à candidatures Fellowships 2026",
        "url": "https://anrs.fr/financements/tous-les-appels-a-projets/aap-fellowships-2026/",
        "date_raw": "25 mars 2026",
        "statut": "ouvert",
    }
    result = s.normalize(raw)
    assert result.source == "ANRS"
    assert result.date_limite == date(2026, 3, 25)
    assert result.statut == "ouvert"
    assert "VIH" in result.mots_cles


def test_normalize_closed():
    s = make_scraper()
    raw = {
        "titre": "AAP VIH/SIDA 2025",
        "url": "https://anrs.fr/financements/tous-les-appels-a-projets/aap-vih-2025/",
        "date_raw": "28 février 2025",
        "statut": "fermé",
    }
    result = s.normalize(raw)
    assert result.statut == "fermé"
    assert result.date_limite == date(2025, 2, 28)


def test_fetch_paginates():
    s = make_scraper()
    pages = {
        s.base_url: SAMPLE_HTML_P1,
        f"{s.base_url}page/2/": SAMPLE_HTML_P2,
    }

    with patch.object(s, "_get", side_effect=lambda url: pages.get(url, "<html><body></body></html>")):
        items = s.fetch()

    assert len(items) == 3


def test_fetch_stops_without_next_page():
    s = make_scraper()
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML_P2  # no /page/2/ link

    with patch.object(s, "_get", side_effect=fake_get):
        s.fetch()

    assert call_count == 1
