from datetime import date
from unittest.mock import patch

from scrapers.frm import FrmScraper

SAMPLE_HTML = """
<html><body>
<main>
  <ul class="ProgramsSection_programs__5__om">
    <li class="program">
      <details class="Program_wrapper__V0mzH" id="amorcage-de-jeunes-equipes-2026">
        <summary class="Program_summary__Sgmmz">
          <h3 class="Program_title__6kWsz">Amorçage de jeunes équipes 2026</h3>
          <ul class="Program_tags__9y6QS">
            <li class="Program_tag__kwMDn">Programme généraliste</li>
          </ul>
          <p class="Program_date__Ahfpg">Date de clôture : 10 avril 2026</p>
        </summary>
        <div class="Program_description__j4nNH">
          <p>L'appel à projets « Amorçage de jeunes équipes FRM » est destiné aux jeunes chercheurs.</p>
        </div>
      </details>
    </li>
    <li class="program">
      <details class="Program_wrapper__V0mzH" id="environnement-et-sante-2026">
        <summary class="Program_summary__Sgmmz">
          <h3 class="Program_title__6kWsz">Environnement et santé 2026</h3>
          <ul class="Program_tags__9y6QS">
            <li class="Program_tag__kwMDn">Programme thématique</li>
          </ul>
          <p class="Program_date__Ahfpg">Date de clôture : 23 avril 2026</p>
        </summary>
        <div class="Program_description__j4nNH">
          <p>Exposition chronique à des agents environnementaux et santé humaine.</p>
        </div>
      </details>
    </li>
    <li class="program">
      <details class="Program_wrapper__V0mzH" id="poste-these-2025">
        <summary class="Program_summary__Sgmmz">
          <h3 class="Program_title__6kWsz">Poste de thèse 2025</h3>
          <ul class="Program_tags__9y6QS">
            <li class="Program_tag__kwMDn">Programme généraliste</li>
          </ul>
          <p class="Program_date__Ahfpg Program_disable__DkwF6">Date de clôture : 19 mars 2025</p>
        </summary>
        <div class="Program_description__j4nNH">
          <p>Programme 2025 — clôturé.</p>
        </div>
      </details>
    </li>
    <li class="program">
      <details class="Program_wrapper__V0mzH" id="espoirs-recherche">
        <summary class="Program_summary__Sgmmz">
          <h3 class="Program_title__6kWsz">Espoirs de la recherche 2026</h3>
          <ul class="Program_tags__9y6QS">
            <li class="Program_tag__kwMDn">Programme généraliste</li>
          </ul>
        </summary>
        <div class="Program_description__j4nNH">
          <p>Programme sans date de clôture fixée.</p>
        </div>
      </details>
    </li>
  </ul>
</main>
</body></html>
"""


def make_scraper():
    return FrmScraper()


def test_parse_extracts_items():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert len(items) == 4
    assert items[0]["titre"] == "Amorçage de jeunes équipes 2026"


def test_parse_url_uses_anchor():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["url"] == "https://www.frm.org/fr/programmes#amorcage-de-jeunes-equipes-2026"
    assert items[1]["url"] == "https://www.frm.org/fr/programmes#environnement-et-sante-2026"


def test_parse_date_extraction():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["date_raw"] == "10 avril 2026"
    assert items[1]["date_raw"] == "23 avril 2026"


def test_parse_status_open():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["statut"] == "ouvert"
    assert items[1]["statut"] == "ouvert"


def test_parse_status_closed_via_disable_class():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[2]["statut"] == "fermé"


def test_parse_status_no_date_defaults_open():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[3]["statut"] == "ouvert"
    assert items[3]["date_raw"] == ""


def test_parse_description():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert "Amorçage de jeunes équipes FRM" in items[0]["description"]


def test_parse_category_tag():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["categorie"] == "Programme généraliste"
    assert items[1]["categorie"] == "Programme thématique"


def test_normalize_open():
    s = make_scraper()
    raw = {
        "titre": "Amorçage de jeunes équipes 2026",
        "url": "https://www.frm.org/fr/programmes#amorcage-de-jeunes-equipes-2026",
        "date_raw": "10 avril 2026",
        "statut": "ouvert",
        "description": "Financement pour jeunes chercheurs.",
        "categorie": "Programme généraliste",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 4, 10)
    assert result.source == "FRM"
    assert result.statut == "ouvert"
    assert result.domaine == "recherche médicale"


def test_normalize_closed():
    s = make_scraper()
    raw = {
        "titre": "Poste de thèse 2025",
        "url": "https://www.frm.org/fr/programmes#poste-these-2025",
        "date_raw": "19 mars 2025",
        "statut": "fermé",
        "description": "",
        "categorie": "Programme généraliste",
    }
    result = s.normalize(raw)
    assert result.statut == "fermé"
    assert result.date_limite == date(2025, 3, 19)


def test_fetch_calls_parse():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    assert len(items) == 4
