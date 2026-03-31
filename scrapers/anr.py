import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://anr.fr"


class AnrScraper(BaseScraper):
    source_name = "ANR"
    base_url = f"{BASE}/fr/appels-ouverts/"

    def fetch(self) -> list[dict]:
        items: list[dict] = []
        page = 0  # ANR uses 0-indexed tx_solr[page] param; page 0 = no param

        while True:
            url = self.base_url if page == 0 else f"{self.base_url}?tx_solr%5Bpage%5D={page}"
            html = self._get(url)
            soup = self._soup(html)

            results = soup.select("div.tx-solr-results-item")
            if not results:
                break

            for item in results:
                title_tag = item.select_one("h3.tx-solr-results-title a")
                dates_tag = item.select_one("p.tx-solr-results-dates")
                desc_tag = item.select_one("p.tx-solr-results-description")
                type_tag = item.select_one("p.tx-solr-results-type")

                if not title_tag:
                    continue

                items.append({
                    "titre": title_tag.get_text(strip=True),
                    "url": BASE + title_tag["href"],
                    "dates_raw": dates_tag.get_text(strip=True) if dates_tag else "",
                    "description": desc_tag.get_text(strip=True) if desc_tag else "",
                    "type": type_tag.get_text(strip=True) if type_tag else "",
                })

            # Check if there's a next page
            next_page = soup.select_one(f'ul.pagination a[href*="tx_solr%5Bpage%5D={page + 1}"]')
            if not next_page:
                break
            page += 1

        return items

    def parse(self, html: str) -> list[dict]:
        # Parsing is done inline in fetch() for this scraper
        return []

    def normalize(self, raw: dict) -> AppelOffre:
        # Dates field: "DD/MM/YYYY - DD/MM/YYYY" (open - close)
        date_limite = None
        dates_raw = raw.get("dates_raw", "")
        if " - " in dates_raw:
            parts = [p.strip() for p in dates_raw.split(" - ")]
            # Second date is the closing date
            date_limite = normalize_date(parts[1]) if len(parts) > 1 else None
        else:
            date_limite = normalize_date(dates_raw)

        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=date_limite,
            eligibilite=raw.get("description", ""),
            domaine="recherche",
            mots_cles=_extract_keywords(raw.get("titre", "") + " " + raw.get("type", "")),
        )


def _extract_keywords(text: str) -> list[str]:
    keywords = []
    patterns = [
        (r"\bsanté\b", "santé"),
        (r"\bcancer\b", "cancer"),
        (r"\bnumérique\b", "numérique"),
        (r"\brecherche\b", "recherche"),
        (r"\binnovation\b", "innovation"),
        (r"\benvironnement\b", "environnement"),
    ]
    for pattern, kw in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            keywords.append(kw)
    return keywords
