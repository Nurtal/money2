import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://www.cancer.fr"

# Real structure (verified 2026-04):
#   URL     : https://www.cancer.fr/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets
#   Cards   : li.list-articles-item
#   Title   : h2 a  (relative URL → prepend BASE)
#   Date    : <time datetime="YYYY-MM-DDCEST…">  → first 10 chars = ISO date
#   Status  : first <p> in .card-start  ("En cours", "Clos", "Résultats")
#   Desc    : <p> in .card-end
#   Pager   : a[href*="?page=N"]  (1-indexed, page 1 has no param)

_STATUS_MAP = {
    "en cours": "ouvert",
    "ouvert": "ouvert",
    "clos": "fermé",
    "clôturé": "fermé",
    "fermé": "fermé",
    "résultats": "fermé",
    "résultat": "fermé",
}


class IncaScraper(BaseScraper):
    source_name = "INCa"
    base_url = f"{BASE}/professionnels-de-la-recherche/appels-a-projets-et-a-candidatures/nos-appels-a-projets"

    def fetch(self) -> list[dict]:
        items: list[dict] = []
        page = 1

        while True:
            url = self.base_url if page == 1 else f"{self.base_url}?page={page}"
            html = self._get(url)
            raw = self.parse(html)
            if not raw:
                break
            items.extend(raw)

            soup = self._soup(html)
            next_link = soup.select_one(f'a[href*="?page={page + 1}"]')
            if not next_link:
                break
            page += 1

        return items

    def parse(self, html: str) -> list[dict]:
        soup = self._soup(html)
        items = []

        for li in soup.select("li.list-articles-item"):
            title_tag = li.select_one("h2 a") or li.select_one("h3 a")
            if not title_tag:
                continue

            # ISO date from <time datetime="YYYY-MM-DDCEST…">
            date_raw = ""
            time_tag = li.select_one("time[datetime]")
            if time_tag:
                date_raw = time_tag["datetime"][:10]  # "YYYY-MM-DD"

            # Status: first <p> inside .card-start
            statut = "ouvert"
            card_start = li.select_one(".card-start")
            if card_start:
                first_p = card_start.select_one("p")
                if first_p:
                    txt = first_p.get_text(strip=True).lower()
                    statut = _STATUS_MAP.get(txt, "ouvert")

            # Description: <p> inside .card-end
            description = ""
            card_end = li.select_one(".card-end")
            if card_end:
                desc_p = card_end.select_one("p")
                if desc_p:
                    description = desc_p.get_text(strip=True)

            items.append({
                "titre": title_tag.get_text(strip=True),
                "url": BASE + title_tag["href"],
                "date_raw": date_raw,
                "statut": statut,
                "description": description,
            })

        return items

    def normalize(self, raw: dict) -> AppelOffre:
        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=normalize_date(raw.get("date_raw")),
            eligibilite=raw.get("description", ""),
            statut=raw.get("statut", "ouvert"),
            domaine="oncologie",
            mots_cles=["cancer", "oncologie"],
        )
