import json
from datetime import date
from unittest.mock import patch

from scrapers.horizon_europe import HorizonEuropeScraper

BASE_PORTAL = (
    "https://ec.europa.eu/info/funding-tenders/opportunities/portal"
    "/screen/opportunities/topic-details"
)

SAMPLE_RESPONSE = json.dumps({
    "totalResults": 2,
    "results": [
        {
            "identifier": "HORIZON-HLTH-2026-DISEASE-04-01",
            "title": "Novel therapeutic approaches for rare diseases",
            "callTitle": "Innovative Health Research 2026",
            "deadlineDate": "2026-05-27T17:00:00",
            "status": "open",
            "programmePart": "Cluster 1 - Health",
            "budgetMin": 3000000.0,
            "budgetMax": 6000000.0,
        },
        {
            "identifier": "HORIZON-HLTH-2026-CANCER-01-01",
            "title": "Immunotherapy combination strategies for solid tumours",
            "callTitle": "Cancer Research Missions 2026",
            "deadlineDate": "2026-09-15T17:00:00",
            "status": "upcoming",
            "programmePart": "Cluster 1 - Health",
            "budgetMin": None,
            "budgetMax": 8000000.0,
        },
    ],
})

EMPTY_RESPONSE = json.dumps({"totalResults": 0, "results": []})
FULL_PAGE_RESPONSE = json.dumps({
    "totalResults": 50,
    "results": [
        {
            "identifier": f"HORIZON-HLTH-2026-X-{i:02d}",
            "title": f"Topic {i}",
            "callTitle": "Call",
            "deadlineDate": "2026-06-01T17:00:00",
            "status": "open",
            "programmePart": "Cluster 1 - Health",
        }
        for i in range(50)
    ],
})


def make_scraper():
    return HorizonEuropeScraper()


def test_parse_extracts_items():
    s = make_scraper()
    items = s.parse(SAMPLE_RESPONSE)
    assert len(items) == 2
    assert items[0]["titre"] == "Novel therapeutic approaches for rare diseases"


def test_parse_url_construction():
    s = make_scraper()
    items = s.parse(SAMPLE_RESPONSE)
    assert items[0]["url"] == f"{BASE_PORTAL}/HORIZON-HLTH-2026-DISEASE-04-01"
    assert items[1]["url"] == f"{BASE_PORTAL}/HORIZON-HLTH-2026-CANCER-01-01"


def test_parse_date_raw():
    s = make_scraper()
    items = s.parse(SAMPLE_RESPONSE)
    assert items[0]["date_raw"] == "2026-05-27T17:00:00"
    assert items[1]["date_raw"] == "2026-09-15T17:00:00"


def test_parse_status_open():
    s = make_scraper()
    items = s.parse(SAMPLE_RESPONSE)
    assert items[0]["statut"] == "ouvert"


def test_parse_status_upcoming():
    s = make_scraper()
    items = s.parse(SAMPLE_RESPONSE)
    assert items[1]["statut"] == "à venir"


def test_parse_status_closed():
    s = make_scraper()
    closed = json.dumps({"results": [{"identifier": "X", "title": "T",
                                       "callTitle": "", "deadlineDate": "",
                                       "status": "closed"}]})
    items = s.parse(closed)
    assert items[0]["statut"] == "fermé"


def test_parse_description():
    s = make_scraper()
    items = s.parse(SAMPLE_RESPONSE)
    assert items[0]["description"] == "Innovative Health Research 2026"


def test_parse_budget():
    s = make_scraper()
    items = s.parse(SAMPLE_RESPONSE)
    assert items[0]["montant_min"] == 3000000.0
    assert items[0]["montant_max"] == 6000000.0


def test_parse_empty_results():
    s = make_scraper()
    items = s.parse(EMPTY_RESPONSE)
    assert items == []


def test_parse_invalid_json():
    s = make_scraper()
    items = s.parse("not-json")
    assert items == []


def test_normalize_date():
    s = make_scraper()
    raw = {
        "titre": "Topic",
        "url": f"{BASE_PORTAL}/HORIZON-X",
        "date_raw": "2026-05-27T17:00:00",
        "statut": "ouvert",
        "description": "",
        "montant_min": None,
        "montant_max": None,
    }
    result = s.normalize(raw)
    assert result.date_limite == date(2026, 5, 27)


def test_normalize_missing_date():
    s = make_scraper()
    raw = {
        "titre": "Topic",
        "url": f"{BASE_PORTAL}/HORIZON-X",
        "date_raw": "",
        "statut": "ouvert",
        "description": "",
        "montant_min": None,
        "montant_max": None,
    }
    assert s.normalize(raw).date_limite is None


def test_normalize_budget():
    s = make_scraper()
    raw = {
        "titre": "Topic",
        "url": f"{BASE_PORTAL}/HORIZON-X",
        "date_raw": "",
        "statut": "ouvert",
        "description": "",
        "montant_min": 3000000.0,
        "montant_max": 6000000.0,
    }
    result = s.normalize(raw)
    assert result.montant_min == 3000000.0
    assert result.montant_max == 6000000.0


def test_normalize_source_and_domain():
    s = make_scraper()
    raw = {
        "titre": "Topic",
        "url": f"{BASE_PORTAL}/HORIZON-X",
        "date_raw": "",
        "statut": "ouvert",
        "description": "",
        "montant_min": None,
        "montant_max": None,
    }
    result = s.normalize(raw)
    assert result.source == "Horizon Europe"
    assert result.domaine == "recherche biomédicale"
    assert "Horizon Europe" in result.mots_cles


def test_fetch_single_page_stops():
    """Fewer results than PAGE_SIZE → only one API call."""
    s = make_scraper()
    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        return SAMPLE_RESPONSE  # 2 results < 50 → stops

    with patch.object(s, "_get", side_effect=fake_get):
        items = s.fetch()

    assert call_count == 1
    assert len(items) == 2


def test_fetch_paginates_on_full_page():
    """Full page (50 results) → fetches next page."""
    s = make_scraper()
    calls = []

    def fake_get(url):
        calls.append(url)
        if "pageNumber=1" in url:
            return FULL_PAGE_RESPONSE
        return EMPTY_RESPONSE  # page 2 empty → stops

    with patch.object(s, "_get", side_effect=fake_get):
        items = s.fetch()

    assert len(calls) == 2
    assert len(items) == 50
