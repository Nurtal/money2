from datetime import date
from unittest.mock import call, patch

from scrapers.ars import ARS_REGIONS, ArsScraper

# HTML matching real ARS structure (verified 2026-04) — same Drupal theme across all regions
SAMPLE_HTML = """
<html><body>
<div class="accueil-appels-projets">
  <div class="container">

    <div class="accueil-appels-projets--item">
      <h3 class="accueil-appels-projets--item-titre">
        <a href="/creation-de-centre-de-ressources-territorial-des-vosges">
          Centre de Ressources Territorial Vosges
        </a>
      </h3>
      <div class="accueil-appels-projets--item--type-appel">
        <p class="field">Appel à candidatures</p>
      </div>
      <div class="accueil-appels-projets--item--description">
        <p>Cet appel vise à renforcer la couverture territoriale en Centre de Ressources Territorial.</p>
      </div>
      <div class="accueil-appels-projets--item--infos">
        <div class="row">
          <div class="col-sm-6"><p>Clôture le 08/04/2026</p></div>
        </div>
      </div>
    </div>

    <div class="accueil-appels-projets--item">
      <h3 class="accueil-appels-projets--item-titre">
        <a href="/infirmiers-en-pratique-avancee-2026">
          Infirmiers en Pratique Avancée
        </a>
      </h3>
      <div class="accueil-appels-projets--item--type-appel">
        <p class="field">Appel à projets</p>
      </div>
      <div class="accueil-appels-projets--item--description">
        <p>Financement de postes d'infirmiers en pratique avancée dans les établissements de santé.</p>
      </div>
      <div class="accueil-appels-projets--item--infos">
        <div class="row">
          <div class="col-sm-6"><p>Clôture le 11/05/2026</p></div>
        </div>
      </div>
    </div>

    <!-- Card without a date -->
    <div class="accueil-appels-projets--item">
      <h3 class="accueil-appels-projets--item-titre">
        <a href="/aap-sans-date">AAP sans date de clôture</a>
      </h3>
      <div class="accueil-appels-projets--item--description">
        <p>Description sans date.</p>
      </div>
      <div class="accueil-appels-projets--item--infos">
        <div class="row"><div class="col-sm-6"><p>Date à préciser</p></div></div>
      </div>
    </div>

  </div>
</div>
</body></html>
"""

EMPTY_HTML = "<html><body><div></div></body></html>"


def make_scraper():
    return ArsScraper()


def test_parse_extracts_items():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert len(items) == 3


def test_parse_titles():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["titre"] == "Centre de Ressources Territorial Vosges"
    assert items[1]["titre"] == "Infirmiers en Pratique Avancée"


def test_parse_urls_absolute():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["url"] == f"{s.base_url}/creation-de-centre-de-ressources-territorial-des-vosges"
    assert items[1]["url"] == f"{s.base_url}/infirmiers-en-pratique-avancee-2026"


def test_parse_date_raw():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["date_raw"] == "08/04/2026"
    assert items[1]["date_raw"] == "11/05/2026"


def test_parse_missing_date():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[2]["date_raw"] == ""


def test_parse_description():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert "Centre de Ressources" in items[0]["description"]


def test_normalize_date():
    s = make_scraper()
    raw = {
        "titre": "Infirmiers en Pratique Avancée",
        "url": "https://www.grand-est.ars.sante.fr/infirmiers-en-pratique-avancee-2026",
        "date_raw": "11/05/2026",
        "description": "",
        "source": "ARS Grand Est",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 5, 11)
    assert result.source == "ARS Grand Est"
    assert result.domaine == "santé / médico-social"


def test_normalize_missing_date():
    s = make_scraper()
    raw = {
        "titre": "AAP sans date",
        "url": "https://www.grand-est.ars.sante.fr/aap-sans-date",
        "date_raw": "",
        "source": "ARS Grand Est",
    }
    result = s.normalize(raw)
    assert result.date_limite is None


def test_fetch_queries_all_regions():
    s = make_scraper()
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML

    with patch.object(s, "_get", side_effect=fake_get):
        items = s.fetch()

    assert call_count == len(ARS_REGIONS)
    # 3 items per region (from SAMPLE_HTML)
    assert len(items) == 3 * len(ARS_REGIONS)


def test_fetch_skips_failed_regions():
    s = make_scraper()

    def fake_get(url):
        if "grand-est" in url:
            raise ConnectionError("timeout")
        return EMPTY_HTML

    with patch.object(s, "_get", side_effect=fake_get):
        items = s.fetch()  # must not raise

    assert isinstance(items, list)


def test_fetch_attaches_region_source():
    s = make_scraper()
    grand_est_html = SAMPLE_HTML
    other_html = EMPTY_HTML

    def fake_get(url):
        if "grand-est" in url:
            return grand_est_html
        return other_html

    with patch.object(s, "_get", side_effect=fake_get):
        items = s.fetch()

    assert any(i["source"] == "ARS Grand Est" for i in items)
