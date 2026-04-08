from datetime import date
from unittest.mock import patch

from scrapers.erc import ErcScraper

BASE = "https://erc.europa.eu"

SAMPLE_HTML = """
<html><body>
<div class="view-content">
  <div class="views-row">
    <h3 class="node__title">
      <a href="/apply-grant/open-calls/erc-2026-stg">ERC Starting Grants 2026 (ERC-2026-STG)</a>
    </h3>
    <div class="field--name-field-deadline">
      <time datetime="2026-10-08T17:00:00+02:00">8 October 2026</time>
    </div>
    <div class="field--name-body">
      <p>Starting Grants support up-and-coming research leaders who are 2–7 years from PhD.</p>
    </div>
  </div>
  <div class="views-row">
    <h3 class="node__title">
      <a href="/apply-grant/open-calls/erc-2026-cog">ERC Consolidator Grants 2026 (ERC-2026-COG)</a>
    </h3>
    <div class="field--name-field-deadline">
      <time datetime="2026-03-12T17:00:00+01:00">12 March 2026</time>
    </div>
    <div class="field--name-body">
      <p>Consolidator Grants support researchers 7–12 years from PhD to consolidate their team.</p>
    </div>
  </div>
  <div class="views-row">
    <h3 class="node__title">
      <a href="/apply-grant/open-calls/erc-2026-poc">ERC Proof of Concept 2026 (ERC-2026-PoC2)</a>
    </h3>
    <div class="field--name-field-deadline">
      <time datetime="2026-09-03T17:00:00+02:00">3 September 2026</time>
    </div>
    <div class="field--name-body">
      <p>PoC grants help ERC grantees explore the commercial potential of their research.</p>
    </div>
  </div>
</div>
</body></html>
"""

EMPTY_HTML = "<html><body><div class='view-content'></div></body></html>"


def make_scraper():
    return ErcScraper()


def test_parse_extracts_items():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert len(items) == 3


def test_parse_titles():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["titre"] == "ERC Starting Grants 2026 (ERC-2026-STG)"
    assert items[1]["titre"] == "ERC Consolidator Grants 2026 (ERC-2026-COG)"


def test_parse_urls_absolute():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert items[0]["url"] == f"{BASE}/apply-grant/open-calls/erc-2026-stg"
    assert items[1]["url"] == f"{BASE}/apply-grant/open-calls/erc-2026-cog"


def test_parse_date_from_time_attribute():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    # Only first 10 chars of datetime attribute → YYYY-MM-DD
    assert items[0]["date_raw"] == "2026-10-08"
    assert items[1]["date_raw"] == "2026-03-12"
    assert items[2]["date_raw"] == "2026-09-03"


def test_parse_description():
    s = make_scraper()
    items = s.parse(SAMPLE_HTML)
    assert "2–7 years from PhD" in items[0]["description"]
    assert "7–12 years from PhD" in items[1]["description"]


def test_parse_empty_html():
    s = make_scraper()
    items = s.parse(EMPTY_HTML)
    assert items == []


def test_normalize_starting_grant():
    s = make_scraper()
    raw = {
        "titre": "ERC Starting Grants 2026 (ERC-2026-STG)",
        "url": f"{BASE}/apply-grant/open-calls/erc-2026-stg",
        "date_raw": "2026-10-08",
        "description": "Starting Grants support up-and-coming research leaders.",
    }
    result = s.normalize(raw)
    assert result.source == "ERC"
    assert result.date_limite == date(2026, 10, 8)
    assert result.domaine == "recherche fondamentale"
    assert "ERC Starting Grant" in result.mots_cles


def test_normalize_consolidator_grant():
    s = make_scraper()
    raw = {
        "titre": "ERC Consolidator Grants 2026 (ERC-2026-COG)",
        "url": f"{BASE}/apply-grant/open-calls/erc-2026-cog",
        "date_raw": "2026-03-12",
        "description": "",
    }
    result = s.normalize(raw)
    assert "ERC Consolidator Grant" in result.mots_cles


def test_normalize_proof_of_concept():
    s = make_scraper()
    raw = {
        "titre": "ERC Proof of Concept 2026",
        "url": f"{BASE}/apply-grant/open-calls/erc-2026-poc",
        "date_raw": "2026-09-03",
        "description": "",
    }
    result = s.normalize(raw)
    assert "ERC Proof of Concept" in result.mots_cles


def test_normalize_unknown_grant_type():
    s = make_scraper()
    raw = {
        "titre": "ERC Special Programme 2026",
        "url": f"{BASE}/apply-grant/open-calls/erc-2026-sp",
        "date_raw": "",
        "description": "",
    }
    result = s.normalize(raw)
    assert "ERC Grant" in result.mots_cles


def test_normalize_missing_date():
    s = make_scraper()
    raw = {
        "titre": "ERC Starting Grants 2026",
        "url": f"{BASE}/apply-grant/open-calls/erc-2026-stg",
        "date_raw": "",
        "description": "",
    }
    assert s.normalize(raw).date_limite is None


def test_normalize_status_always_open():
    """ERC open-calls page only lists active calls — statut is always 'ouvert'."""
    s = make_scraper()
    raw = {
        "titre": "ERC Advanced Grants 2026",
        "url": f"{BASE}/apply-grant/open-calls/erc-2026-adg",
        "date_raw": "2026-08-28",
        "description": "",
    }
    result = s.normalize(raw)
    assert result.statut == "ouvert"


def test_fetch_calls_parse():
    s = make_scraper()
    with patch.object(s, "_get", return_value=SAMPLE_HTML):
        items = s.fetch()
    assert len(items) == 3
    assert items[0]["titre"] == "ERC Starting Grants 2026 (ERC-2026-STG)"
