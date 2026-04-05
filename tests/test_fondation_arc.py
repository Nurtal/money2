from datetime import date
from unittest.mock import patch

from scrapers.fondation_arc import FondationArcScraper

# HTML matching real Fondation ARC structure (verified 2026-04)
SAMPLE_HTML = """
<html><body>
<main class="main">

  <!-- Featured/highlighted card -->
  <div class="c-highlighting">
    <div class="container">
      <div class="c-highlighting__container">
        <div class="c-highlighting__head">
          <h2 class="h2">Soutien aux Manifestations Scientifiques 2026</h2>
        </div>
        <div class="c-highlighting__content">
          <div class="c-highlighting__text">
            <div class="c-cardProject__intro">
              <div class="c-cardProject__intro-title">Appel à projets ouvert</div>
              <p>Date de limite de remise des dossiers :<br/><strong>04 mai 2026</strong></p>
            </div>
            <p>Mission d'information sur les avancées de la recherche.</p>
            <a class="c-button blue small" href="https://www.fondation-arc.org/appels-a-projets/soutien-sms/">
              <span>En savoir plus</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- List cards -->
  <div class="c-listCards">
    <div class="container">
      <ul class="c-listCards__container">
        <li class="c-cardProject c-card yellow">
          <div class="c-cardProject__content">
            <div class="h5">Prix Kerner 2026</div>
            <div class="c-tags"><span>Action scientifique</span><span>Jeunes chercheurs</span></div>
            <a class="c-buttonIcon" href="https://www.fondation-arc.org/appels-a-projets/prix-kerner-2026/">
              <span class="visuallyHidden">En savoir plus sur Prix Kerner 2026</span>
            </a>
          </div>
          <div class="c-cardProject__intro">
            <div class="c-cardProject__intro-title">Appel à projets à venir</div>
            <p>Date de limite de remise des dossiers :<br/><strong>01 juin 2026</strong></p>
          </div>
        </li>
        <li class="c-cardProject c-card blue">
          <div class="c-cardProject__content">
            <div class="h5">PANCRÉAS 2026</div>
            <div class="c-tags"><span>Action scientifique</span></div>
            <a class="c-buttonIcon" href="https://www.fondation-arc.org/appels-a-projets/pancreas-2026/">
              <span class="visuallyHidden">En savoir plus sur PANCRÉAS 2026</span>
            </a>
          </div>
          <div class="c-cardProject__intro">
            <div class="c-cardProject__intro-title">Appel à projets ouvert</div>
            <p>Date de limite de remise des dossiers :<br/><strong>11 juin 2026</strong></p>
          </div>
        </li>
        <li class="c-cardProject c-card red">
          <div class="c-cardProject__content">
            <div class="h5">Post-doctorants en France</div>
            <div class="c-tags"><span>Jeunes chercheurs</span><span>Soutien</span></div>
            <a class="c-buttonIcon" href="https://www.fondation-arc.org/appels-a-projets/post-doctorants-en-france/">
              <span class="visuallyHidden">En savoir plus</span>
            </a>
          </div>
          <div class="c-cardProject__intro">
            <div class="c-cardProject__intro-title">Appel à projets fermé</div>
            <p>Date de limite de remise des dossiers :<br/><strong>03 février 2026</strong></p>
          </div>
        </li>
      </ul>
    </div>
  </div>

  <!-- Pagination -->
  <a href="https://www.fondation-arc.org/appels-a-projets/page/2/">2</a>

</main>
</body></html>
"""

SAMPLE_HTML_P2 = """
<html><body>
<main class="main">
  <div class="c-listCards">
    <div class="container">
      <ul class="c-listCards__container">
        <li class="c-cardProject c-card yellow">
          <div class="c-cardProject__content">
            <div class="h5">SIGN'IT 2026</div>
            <div class="c-tags"><span>Action scientifique</span></div>
            <a class="c-buttonIcon" href="https://www.fondation-arc.org/appels-a-projets/signit-2026/">
              <span class="visuallyHidden">En savoir plus</span>
            </a>
          </div>
          <div class="c-cardProject__intro">
            <div class="c-cardProject__intro-title">Appel à projets ouvert</div>
            <p>Date de limite de remise des dossiers :<br/><strong>15 juillet 2026</strong></p>
          </div>
        </li>
      </ul>
    </div>
  </div>
</main>
</body></html>
"""


def make_scraper():
    return FondationArcScraper()


def test_parse_extracts_highlighted_and_list():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    # 1 highlighted + 3 list cards
    assert len(items) == 4
    assert items[0]["titre"] == "Soutien aux Manifestations Scientifiques 2026"


def test_parse_list_titles():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[1]["titre"] == "Prix Kerner 2026"
    assert items[2]["titre"] == "PANCRÉAS 2026"


def test_parse_urls():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["url"] == "https://www.fondation-arc.org/appels-a-projets/soutien-sms/"
    assert items[1]["url"] == "https://www.fondation-arc.org/appels-a-projets/prix-kerner-2026/"


def test_parse_date_raw():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["date_raw"] == "04 mai 2026"
    assert items[1]["date_raw"] == "01 juin 2026"
    assert items[2]["date_raw"] == "11 juin 2026"


def test_parse_status_open():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["statut"] == "ouvert"
    assert items[2]["statut"] == "ouvert"


def test_parse_status_a_venir():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[1]["statut"] == "à venir"


def test_parse_status_ferme():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[3]["statut"] == "fermé"


def test_parse_tags():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert "Action scientifique" in items[1]["tags"]
    assert "Jeunes chercheurs" in items[1]["tags"]


def test_normalize():
    s = make_scraper()
    raw = {
        "titre": "PANCRÉAS 2026",
        "url": "https://www.fondation-arc.org/appels-a-projets/pancreas-2026/",
        "date_raw": "11 juin 2026",
        "statut": "ouvert",
        "tags": ["Action scientifique"],
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 6, 11)
    assert result.source == "Fondation ARC"
    assert result.domaine == "oncologie"
    assert "cancer" in result.mots_cles
    assert "Action scientifique" in result.mots_cles


def test_normalize_ferme():
    s = make_scraper()
    raw = {
        "titre": "Post-doctorants en France",
        "url": "https://www.fondation-arc.org/appels-a-projets/post-doctorants-en-france/",
        "date_raw": "03 février 2026",
        "statut": "fermé",
        "tags": [],
    }
    result = s.normalize(raw)
    assert result.statut == "fermé"
    assert result.date_limite == date(2026, 2, 3)


def test_fetch_paginates():
    s = make_scraper()
    pages = {
        s.base_url: SAMPLE_HTML,
        f"{s.base_url}page/2/": SAMPLE_HTML_P2,
    }
    with patch.object(s, "_get", side_effect=lambda url: pages.get(url, "<html><body></body></html>")):
        items = s.fetch()
    assert len(items) == 5


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
