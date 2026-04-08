import json
import urllib.parse

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE_PORTAL = (
    "https://ec.europa.eu/info/funding-tenders/opportunities/portal"
    "/screen/opportunities/topic-details"
)
API_BASE = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"

# EU Funding & Tenders Portal Search API (public, no auth required):
#   GET https://api.tech.ec.europa.eu/search-api/prod/rest/search
#       ?apiKey=SEDIA&text=*&pageSize=50&pageNumber=1&languages=en
#       &facets=[{"name":"programmePart","values":["Cluster 1 - Health"]}]
#
#   Response JSON (top-level keys):
#     totalResults : int
#     results      : list of topic objects, each with:
#       identifier    : "HORIZON-HLTH-2026-DISEASE-04-01"
#       title         : "Novel therapeutic approaches for rare diseases"
#       callTitle     : "Innovative Health 2026"
#       deadlineDate  : "2026-05-27T17:00:00"   (ISO 8601, time stripped by normalize_date)
#       status        : "open" | "upcoming" | "closed"
#       programmePart : "Cluster 1 - Health"
#       budgetMin     : 3000000.0  (optional, euros)
#       budgetMax     : 6000000.0  (optional, euros)

_STATUS_MAP = {
    "open": "ouvert",
    "upcoming": "à venir",
    "forthcoming": "à venir",
    "closed": "fermé",
}

_PAGE_SIZE = 50


class HorizonEuropeScraper(BaseScraper):
    source_name = "Horizon Europe"
    base_url = API_BASE

    def fetch(self) -> list[dict]:
        items: list[dict] = []
        page = 1

        while True:
            facets = json.dumps([
                {"name": "programmePart", "values": ["Cluster 1 - Health"]},
                {"name": "status", "values": ["open", "upcoming"]},
            ])
            params = urllib.parse.urlencode({
                "apiKey": "SEDIA",
                "text": "*",
                "pageSize": _PAGE_SIZE,
                "pageNumber": page,
                "languages": "en",
                "facets": facets,
            })
            url = f"{self.base_url}?{params}"
            raw_json = self._get(url)
            batch = self.parse(raw_json)
            if not batch:
                break
            items.extend(batch)
            # Stop when we get fewer results than a full page
            if len(batch) < _PAGE_SIZE:
                break
            page += 1

        return items

    def parse(self, html: str) -> list[dict]:
        try:
            data = json.loads(html)
        except (json.JSONDecodeError, TypeError):
            return []

        items = []
        for r in data.get("results", []):
            identifier = r.get("identifier", "")
            items.append({
                "titre": r.get("title", ""),
                "url": f"{BASE_PORTAL}/{identifier}" if identifier else "",
                "date_raw": r.get("deadlineDate", ""),
                "statut": _STATUS_MAP.get(r.get("status", "").lower(), "ouvert"),
                "description": r.get("callTitle", ""),
                "montant_min": r.get("budgetMin"),
                "montant_max": r.get("budgetMax"),
            })
        return items

    def normalize(self, raw: dict) -> AppelOffre:
        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=normalize_date(raw.get("date_raw", "")),
            eligibilite=raw.get("description", ""),
            statut=raw.get("statut", "ouvert"),
            montant_min=raw.get("montant_min"),
            montant_max=raw.get("montant_max"),
            domaine="recherche biomédicale",
            mots_cles=["Horizon Europe", "santé", "biomedical"],
        )
