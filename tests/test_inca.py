from datetime import date
from unittest.mock import patch

from scrapers.inca import IncaScraper

# HTML matching the real INCa structure (li.list-articles-item / h2 a / time[datetime])
SAMPLE_HTML_P1 = """
<html><body>
<ul class="list-unstyled">
  <li class="list-articles-item mb-md-2 mb-0">
    <div class="card card-inca">
      <div class="card-body p-2">
        <div class="order-4">
          <h2 class="card-title">
            <a href="/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets/seq-rth26">
              AAP Radiothérapie 2026
            </a>
          </h2>
          <div class="card-end">
            <p>Cet appel vise à limiter les séquelles de la radiothérapie.</p>
          </div>
        </div>
        <div class="card-start d-flex">
          <p class="mb-1">En cours</p>
          <p class="mb-1 card-date">Date limite de soumission :
            <time datetime="2026-05-27CEST16:00"><strong>27 mai 2026 à 16:00</strong></time>
          </p>
        </div>
      </div>
    </div>
  </li>
  <li class="list-articles-item mb-md-2 mb-0">
    <div class="card card-inca">
      <div class="card-body p-2">
        <div class="order-4">
          <h2 class="card-title">
            <a href="/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets/aap-test-2">
              AAP Prévention Cancer 2025
            </a>
          </h2>
          <div class="card-end">
            <p>Prévention et dépistage précoce.</p>
          </div>
        </div>
        <div class="card-start d-flex">
          <p class="mb-1">Clos</p>
          <p class="mb-1 card-date">Date limite de soumission :
            <time datetime="2025-04-15CEST16:00"><strong>15 avril 2025 à 16:00</strong></time>
          </p>
        </div>
      </div>
    </div>
  </li>
</ul>
<ul class="pagination">
  <li class="page-item"><a class="page-link" href="/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets?page=2">2</a></li>
</ul>
</body></html>
"""

SAMPLE_HTML_P2 = """
<html><body>
<ul class="list-unstyled">
  <li class="list-articles-item mb-md-2 mb-0">
    <div class="card card-inca">
      <div class="card-body p-2">
        <div class="order-4">
          <h2 class="card-title">
            <a href="/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets/aap-test-3">
              AAP Biomarqueurs 2025
            </a>
          </h2>
          <div class="card-end">
            <p>Recherche sur les biomarqueurs tumoraux.</p>
          </div>
        </div>
        <div class="card-start d-flex">
          <p class="mb-1">En cours</p>
          <p class="mb-1 card-date">Date limite de soumission :
            <time datetime="2025-09-30CEST16:00"><strong>30 septembre 2025 à 16:00</strong></time>
          </p>
        </div>
      </div>
    </div>
  </li>
</ul>
<ul class="pagination">
  <li class="page-item active"><span class="page-link">2</span></li>
</ul>
</body></html>
"""


def make_scraper():
    return IncaScraper()


def test_parse_extracts_items():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert len(items) == 2
    assert items[0]["titre"] == "AAP Radiothérapie 2026"
    assert "seq-rth26" in items[0]["url"]


def test_parse_date_from_time_attribute():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert items[0]["date_raw"] == "2026-05-27"
    assert items[1]["date_raw"] == "2025-04-15"


def test_parse_status_open():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert items[0]["statut"] == "ouvert"


def test_parse_status_closed():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert items[1]["statut"] == "fermé"


def test_parse_description():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML_P1)
    assert items[0]["description"] == "Cet appel vise à limiter les séquelles de la radiothérapie."


def test_normalize_iso_date():
    s = make_scraper()
    raw = {
        "titre": "AAP Radiothérapie 2026",
        "url": "https://www.cancer.fr/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets/seq-rth26",
        "date_raw": "2026-05-27",
        "statut": "ouvert",
        "description": "",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 5, 27)
    assert result.source == "INCa"
    assert result.domaine == "oncologie"
    assert "cancer" in result.mots_cles


def test_normalize_status_closed():
    s = make_scraper()
    raw = {
        "titre": "Test",
        "url": "https://www.cancer.fr/test",
        "date_raw": "2025-04-15",
        "statut": "fermé",
        "description": "",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2025, 4, 15)
    assert result.statut == "fermé"


def test_normalize_resultats_maps_to_ferme():
    """'Résultats' status should map to 'fermé'."""
    s = make_scraper()
    html = SAMPLE_HTML_P1.replace(">En cours<", ">Résultats<")
    items = s.parse(html)
    assert items[0]["statut"] == "fermé"


def test_fetch_paginates():
    s = make_scraper()
    pages = {
        s.base_url: SAMPLE_HTML_P1,
        f"{s.base_url}?page=2": SAMPLE_HTML_P2,
    }

    with patch.object(s, "_get", side_effect=lambda url: pages.get(url, "<html><body><ul></ul></body></html>")):
        items = s.fetch()

    assert len(items) == 3
    titles = [i["titre"] for i in items]
    assert "AAP Radiothérapie 2026" in titles
    assert "AAP Biomarqueurs 2025" in titles


def test_fetch_stops_without_next_page():
    s = make_scraper()
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML_P2  # no ?page=2 link

    with patch.object(s, "_get", side_effect=fake_get):
        s.fetch()

    assert call_count == 1
