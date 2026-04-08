from datetime import date
from unittest.mock import patch

from scrapers.ihi import IhiScraper

BASE = "https://www.ihi.europa.eu"

SAMPLE_HTML = """
<html><body>
<div class="calls-listing">
  <article class="call node--type-call">
    <h2><a href="/apply-funding/open-calls/ihi-2025-22">IHI Call 22 – AI-powered diagnostics</a></h2>
    <time datetime="2025-09-17">17 September 2025</time>
    <span class="status">Open</span>
    <div class="description">
      <p>This call targets AI solutions for early disease detection across multiple indications.</p>
    </div>
  </article>
  <article class="call node--type-call">
    <h2><a href="/apply-funding/open-calls/ihi-2026-23">IHI Call 23 – Antimicrobial resistance</a></h2>
    <time datetime="2026-03-05">5 March 2026</time>
    <span class="status">Upcoming</span>
    <div class="description">
      <p>Targeting new antimicrobial strategies to combat drug-resistant pathogens.</p>
    </div>
  </article>
  <article class="call node--type-call">
    <h2><a href="/apply-funding/open-calls/ihi-2024-20">IHI Call 20 – Rare diseases</a></h2>
    <time datetime="2024-11-14">14 November 2024</time>
    <span class="status">Closed</span>
    <div class="description">
      <p>Supporting innovative therapies for rare and neglected diseases.</p>
    </div>
  </article>
</div>
</body></html>
"""

EMPTY_HTML = "<html><body><div class='calls-listing'></div></body></html>"


def make_scraper():
    return IhiScraper()


def test_parse_extracts_items():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert len(items) == 3


def test_parse_titles():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["titre"] == "IHI Call 22 – AI-powered diagnostics"
    assert items[1]["titre"] == "IHI Call 23 – Antimicrobial resistance"


def test_parse_urls_absolute():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["url"] == f"{BASE}/apply-funding/open-calls/ihi-2025-22"
    assert items[1]["url"] == f"{BASE}/apply-funding/open-calls/ihi-2026-23"


def test_parse_date_from_time_attribute():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["date_raw"] == "2025-09-17"
    assert items[1]["date_raw"] == "2026-03-05"
    assert items[2]["date_raw"] == "2024-11-14"


def test_parse_status_open():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["statut"] == "ouvert"


def test_parse_status_upcoming():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[1]["statut"] == "à venir"


def test_parse_status_closed():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[2]["statut"] == "fermé"


def test_parse_description():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert "AI solutions" in items[0]["description"]
    assert "antimicrobial" in items[1]["description"]


def test_parse_empty_html():
    s = make_scraper()
    items = s.parse(EMPTY_HTML)
    assert items == []


def test_normalize_open():
    s = make_scraper()
    raw = {
        "titre": "IHI Call 22 – AI-powered diagnostics",
        "url": f"{BASE}/apply-funding/open-calls/ihi-2025-22",
        "date_raw": "2025-09-17",
        "statut": "ouvert",
        "description": "This call targets AI solutions for early disease detection.",
    }
    result = s.normalize(raw)
    assert result.source == "IHI"
    assert result.date_limite == date(2025, 9, 17)
    assert result.statut == "ouvert"
    assert result.domaine == "innovation santé"
    assert "IHI" in result.mots_cles


def test_normalize_closed():
    s = make_scraper()
    raw = {
        "titre": "IHI Call 20 – Rare diseases",
        "url": f"{BASE}/apply-funding/open-calls/ihi-2024-20",
        "date_raw": "2024-11-14",
        "statut": "fermé",
        "description": "",
    }
    result = s.normalize(raw)
    assert result.statut == "fermé"
    assert result.date_limite == date(2024, 11, 14)


def test_normalize_missing_date():
    s = make_scraper()
    raw = {
        "titre": "IHI Call",
        "url": f"{BASE}/apply-funding/open-calls/ihi-test",
        "date_raw": "",
        "statut": "ouvert",
        "description": "",
    }
    assert s.normalize(raw).date_limite is None


def test_fetch_calls_parse():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    assert len(items) == 3
    assert items[0]["titre"] == "IHI Call 22 – AI-powered diagnostics"
