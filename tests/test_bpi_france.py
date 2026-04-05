from datetime import date
from unittest.mock import patch

from scrapers.bpi_france import BpiFranceScraper

SAMPLE_HTML = """
<html><body>
<ul class="listing-block">
  <li>
    <div class="article-card card-our-project md-card">
      <div class="desc-block">
        <ul class="option-list">
          <li><span class="rubrique rubrique-project">Appels à projets</span></li>
        </ul>
        <span class="card-date">17/04/2025 au 02/06/2026</span>
        <div class="desc">
          <h3><a href="/nos-appels-a-projets-concours/ami-piiec-sante">AMI PIIEC Santé - TECH4CURE</a></h3>
          <p><a href="/nos-appels-a-projets-concours/ami-piiec-sante">
            Financement pour partenaires indirects du PIIEC Santé.
          </a></p>
        </div>
        <div class="bottom-block">
          <a class="see-more" href="https://www.picxel.bpifrance.fr/" target="_blank">Candidater</a>
        </div>
      </div>
    </div>
  </li>
  <li>
    <div class="article-card card-our-project md-card">
      <div class="desc-block">
        <ul class="option-list">
          <li><span class="rubrique rubrique-project">Appels à projets</span></li>
        </ul>
        <span class="card-date">01/01/2026 au 08/09/2026</span>
        <div class="desc">
          <h3><a href="/nos-appels-a-projets-concours/biotherapies">AAP Innovations en biothérapies</a></h3>
          <p><a href="/nos-appels-a-projets-concours/biotherapies">
            Soutien à l'innovation en biothérapies et bioproduction.
          </a></p>
        </div>
      </div>
    </div>
  </li>
</ul>
</body></html>
"""

SAMPLE_HTML_P2 = """
<html><body>
<ul class="listing-block">
  <li>
    <div class="article-card card-our-project md-card">
      <div class="desc-block">
        <span class="card-date">01/06/2026 au 31/12/2026</span>
        <div class="desc">
          <h3><a href="/nos-appels-a-projets-concours/aap-page2">AAP Prévention Santé</a></h3>
          <p><a href="/nos-appels-a-projets-concours/aap-page2">Description page 2.</a></p>
        </div>
      </div>
    </div>
  </li>
</ul>
</body></html>
"""


def make_scraper():
    return BpiFranceScraper()


def test_fetch_parses_items():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    assert len(items) == 2
    assert items[0]["titre"] == "AMI PIIEC Santé - TECH4CURE"
    assert items[0]["url"] == "https://www.bpifrance.fr/nos-appels-a-projets-concours/ami-piiec-sante"


def test_fetch_date_raw():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    assert items[0]["date_raw"] == "17/04/2025 au 02/06/2026"
    assert items[1]["date_raw"] == "01/01/2026 au 08/09/2026"


def test_normalize_closing_date():
    s = make_scraper()
    raw = {
        "titre": "AMI PIIEC Santé",
        "url": "https://www.bpifrance.fr/nos-appels-a-projets-concours/ami-piiec-sante",
        "date_raw": "17/04/2025 au 02/06/2026",
        "description": "Financement pour partenaires indirects.",
        "categorie": "Appels à projets",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 6, 2)
    assert result.source == "BPI France"


def test_normalize_single_date():
    s = make_scraper()
    raw = {
        "titre": "Test",
        "url": "https://www.bpifrance.fr/test",
        "date_raw": "30/06/2026",
        "description": "",
        "categorie": "",
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 6, 30)


def test_normalize_missing_date():
    s = make_scraper()
    raw = {
        "titre": "Test",
        "url": "https://www.bpifrance.fr/test",
        "date_raw": "",
        "description": "",
        "categorie": "",
    }
    assert s.normalize(raw).date_limite is None


def test_normalize_keywords():
    s = make_scraper()
    raw = {
        "titre": "AAP Innovations en biothérapies et bioproduction",
        "url": "https://www.bpifrance.fr/test",
        "date_raw": "",
        "description": "Soutien à la prévention et l'innovation.",
        "categorie": "",
    }
    result = s.normalize(raw)
    assert "innovation" in result.mots_cles
    assert "prévention" in result.mots_cles
    assert "biothérapie" in result.mots_cles


def test_pagination_stops_without_next():
    s = make_scraper()
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_HTML  # no pager link

    with patch.object(s, "_get", side_effect=fake_get):
        items = s.fetch()

    assert call_count == 1
    assert len(items) == 2


def test_pagination_follows_next_page():
    s = make_scraper()
    # Pager must be inside the body; inserting before </body> so lxml parses it
    html_p1 = SAMPLE_HTML.replace(
        "</body></html>",
        '<ul><li class="pager__item"><a href="?labels=267&amp;page=1">2</a></li></ul></body></html>',
    )

    pages = {
        f"{s.base_url}?labels={s._sante_label}": html_p1,
        f"{s.base_url}?labels={s._sante_label}&page=1": SAMPLE_HTML_P2,
    }

    with patch.object(s, "_get", side_effect=lambda url: pages[url]):
        items = s.fetch()

    assert len(items) == 3
