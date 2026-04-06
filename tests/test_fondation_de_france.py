from datetime import date
from unittest.mock import patch

from scrapers.fondation_de_france import FondationDeFranceScraper

# HTML matching real Fondation de France structure (verified 2026-04)
SAMPLE_HTML = """
<html><body>
<div class="uk-section">

  <!-- Health card 1: cancer research -->
  <div class="uk-width-expand@m">
    <h3>
      <a class="el-link" href="/fr/appels-a-projets/cancer-resistance-traitements">
        Recherche fondamentale et translationnelle sur le cancer
      </a>
    </h3>
    <div class="uk-panel uk-margin">
      <div class="uk-grid">
        <div class="uk-width-1-2@m">
          <div class="uk-panel uk-margin">
            Date d'ouverture : 8 décembre 2025
          </div>
        </div>
        <div class="uk-width-1-2@m">
          <div class="uk-panel uk-margin">
            Date de dépôt des dossiers : 20 mars 2026
          </div>
        </div>
      </div>
    </div>
    <div class="uk-panel uk-margin">
      Les donateurs de la Fondation de France manifestent un intérêt permanent pour les avancées de la lutte contre le cancer.
    </div>
  </div>

  <!-- Health card 2: santé publique -->
  <div class="uk-width-expand@m">
    <h3>
      <a class="el-link" href="/fr/appels-a-projets/sante-publique-et-environnement">
        Santé publique et environnement
      </a>
    </h3>
    <div class="uk-panel uk-margin">
      <div class="uk-grid">
        <div class="uk-width-1-2@m">
          <div class="uk-panel uk-margin">
            Date d'ouverture : 18 décembre 2025
          </div>
        </div>
        <div class="uk-width-1-2@m">
          <div class="uk-panel uk-margin">
            Date de dépôt des dossiers : 18 février 2026
          </div>
        </div>
      </div>
    </div>
    <div class="uk-panel uk-margin">
      L'impact de l'environnement sur la santé humaine est de plus en plus reconnu.
    </div>
  </div>

  <!-- Non-health card: should be filtered out -->
  <div class="uk-width-expand@m">
    <h3>
      <a class="el-link" href="/fr/appels-a-projets/eau-grand-ouest">
        L'eau dans le Grand Ouest : un défi collectif
      </a>
    </h3>
    <div class="uk-panel uk-margin">
      <div class="uk-grid">
        <div class="uk-width-1-2@m">
          <div class="uk-panel uk-margin">
            Date d'ouverture : 23 mars 2026
          </div>
        </div>
        <div class="uk-width-1-2@m">
          <div class="uk-panel uk-margin">
            Date de dépôt des dossiers : 22 mai 2026
          </div>
        </div>
      </div>
    </div>
    <div class="uk-panel uk-margin">
      La Fondation de France Grand Ouest lance un appel à projets visant la préservation et le partage de la ressource en eau.
    </div>
  </div>

  <!-- Health card 3: neurodégénératif -->
  <div class="uk-width-expand@m">
    <h3>
      <a class="el-link" href="/fr/appels-a-projets/maladies-neurodegeneratives">
        Recherche sur les maladies neurodégénératives
      </a>
    </h3>
    <div class="uk-panel uk-margin">
      <div class="uk-grid">
        <div class="uk-width-1-2@m">
          <div class="uk-panel uk-margin">
            Date d'ouverture : 9 juin 2025
          </div>
        </div>
        <div class="uk-width-1-2@m">
          <div class="uk-panel uk-margin">
            Date de dépôt des dossiers : 17 septembre 2025
          </div>
        </div>
      </div>
    </div>
    <div class="uk-panel uk-margin">
      Le vieillissement croissant de la population entraîne une progression des maladies neurodégénératives.
    </div>
  </div>

  <!-- Footer links (no href, should be ignored) -->
  <div class="uk-width-expand@m">
    <h3><a>Un organisme</a></h3>
  </div>

</div>
</body></html>
"""


def make_scraper():
    return FondationDeFranceScraper()


def test_parse_filters_health_only():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    titles = [i["titre"] for i in items]
    assert len(items) == 3
    assert "Recherche fondamentale et translationnelle sur le cancer" in titles
    assert "Santé publique et environnement" in titles
    assert "Recherche sur les maladies neurodégénératives" in titles
    # Non-health card filtered out
    assert all("eau" not in t.lower() for t in titles)


def test_parse_urls():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["url"] == "https://www.fondationdefrance.org/fr/appels-a-projets/cancer-resistance-traitements"
    assert items[1]["url"] == "https://www.fondationdefrance.org/fr/appels-a-projets/sante-publique-et-environnement"


def test_parse_date_raw():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["date_raw"] == "20 mars 2026"
    assert items[1]["date_raw"] == "18 février 2026"


def test_parse_ignores_card_without_href():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    # "Un organisme" has no href, must be ignored
    assert all(i["titre"] != "Un organisme" for i in items)


def test_normalize_date():
    s = make_scraper()
    raw = {
        "titre": "Recherche fondamentale et translationnelle sur le cancer",
        "url": "https://www.fondationdefrance.org/fr/appels-a-projets/cancer-resistance-traitements",
        "date_raw": "20 mars 2026",
        "description": "Lutte contre le cancer.",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 3, 20)
    assert result.source == "Fondation de France"
    assert result.domaine == "santé / recherche médicale"
    assert "cancer" in result.mots_cles


def test_normalize_neuro_keywords():
    s = make_scraper()
    raw = {
        "titre": "Recherche sur les maladies neurodégénératives",
        "url": "https://www.fondationdefrance.org/fr/appels-a-projets/maladies-neurodegeneratives",
        "date_raw": "17 septembre 2025",
        "description": "Progression des maladies neurodégénératives.",
    }
    result = s.normalize(raw)
    assert "neurodégénératif" in result.mots_cles
    assert "maladies" in result.mots_cles


def test_fetch_calls_get_once():
    s = make_scraper()
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML

    with patch.object(s, "_get", side_effect=fake_get):
        items = s.fetch()

    assert call_count == 1
    assert len(items) == 3
