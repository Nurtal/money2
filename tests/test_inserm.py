from datetime import date
from unittest.mock import patch

from scrapers.inserm import InsermScraper, _parse_inserm_date

SAMPLE_HTML = """
<html><body>
<main>
  <article class="event_inserm post-62911632 project_call type-project_call status-publish hentry funding_type-financements-inserm" id="post-62911632">
    <div class="texts-wrapper">
      <div class="entry-header">
        <div class="date"></div>
        <h2 class="entry-title">Psychiatrie de précision</h2>
      </div>
      <div class="entry-content">
        <div class="date">
          <span class="prefix">Date limite :</span>
          30.04.26
        </div>
        <p class="details">Le PEPR Propsy soutient des projets pilotes en psychiatrie de précision.</p>
        <div class="links-date">
          <ul class="links">
            <li><a href="https://www.propsy-edu.fr/appels-a-projets/" target="_blank">En savoir plus</a></li>
          </ul>
        </div>
        <div class="published-date"><span>Publié le</span> 12.03.2026</div>
      </div>
    </div>
  </article>
  <article class="event_inserm post-62911633 project_call type-project_call status-publish hentry funding_type-autres-financements" id="post-62911633">
    <div class="texts-wrapper">
      <div class="entry-header">
        <div class="date"></div>
        <h2 class="entry-title">Cancérologie</h2>
      </div>
      <div class="entry-content">
        <div class="date">
          <span class="prefix">Date limite :</span>
          11.06.26
        </div>
        <p class="details">Fondation ARC soutient des recherches en cancérologie sur le pancréas.</p>
        <div class="links-date">
          <ul class="links">
            <li><a href="https://www.fondation-arc.org/aap-pancreas" target="_blank">En savoir plus</a></li>
          </ul>
        </div>
        <div class="published-date"><span>Publié le</span> 26.03.2026</div>
      </div>
    </div>
  </article>
  <article class="event_inserm post-62911634 project_call type-project_call status-publish hentry" id="post-62911634">
    <div class="texts-wrapper">
      <div class="entry-header">
        <div class="date"></div>
        <h2 class="entry-title">Cardiologie</h2>
      </div>
      <div class="entry-content">
        <div class="date">
          27.05.26
        </div>
        <p class="details">La British Heart Foundation soutient des collaborations internationales.</p>
        <div class="links-date">
          <ul class="links">
            <li><a href="https://www.bhf.org.uk/research" target="_blank">En savoir plus</a></li>
          </ul>
        </div>
      </div>
    </div>
  </article>
</main>
</body></html>
"""


def make_scraper():
    return InsermScraper()


def test_parse_inserm_date_dd_mm_yy():
    assert _parse_inserm_date("30.04.26") == date(2026, 4, 30)
    assert _parse_inserm_date("11.06.26") == date(2026, 6, 11)
    assert _parse_inserm_date("5.05.26") == date(2026, 5, 5)


def test_parse_inserm_date_none():
    assert _parse_inserm_date(None) is None
    assert _parse_inserm_date("") is None


def test_parse_extracts_items():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert len(items) == 3
    assert items[0]["titre"] == "Psychiatrie de précision"
    assert items[1]["titre"] == "Cancérologie"


def test_parse_date_raw():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["date_raw"] == "30.04.26"
    assert items[1]["date_raw"] == "11.06.26"
    assert items[2]["date_raw"] == "27.05.26"


def test_parse_url_from_links():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["url"] == "https://www.propsy-edu.fr/appels-a-projets/"
    assert items[1]["url"] == "https://www.fondation-arc.org/aap-pancreas"


def test_parse_description():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert "psychiatrie de précision" in items[0]["description"].lower()


def test_normalize():
    s = make_scraper()
    raw = {
        "titre": "Psychiatrie de précision",
        "url": "https://www.propsy-edu.fr/appels-a-projets/",
        "date_raw": "30.04.26",
        "description": "Le PEPR Propsy soutient des projets pilotes.",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 4, 30)
    assert result.source == "Inserm"
    assert result.domaine == "recherche biomédicale"
    assert "Inserm" in result.mots_cles


def test_normalize_missing_date():
    s = make_scraper()
    raw = {
        "titre": "Test",
        "url": "https://pro.inserm.fr/test",
        "date_raw": "",
        "description": "",
    }
    assert s.normalize(raw).date_limite is None


def test_fetch_calls_parse():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    assert len(items) == 3
