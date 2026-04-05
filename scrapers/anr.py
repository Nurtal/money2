import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://anr.fr"

# Real structure (verified 2026-04):
#   URL     : https://anr.fr/fr/appels/
#   Cards   : div.card.appel
#   Title   : h2 a
#   Date    : div.date  → "02/04/2026 - 04/06/2026" or "Avril 2026 - Juin 2026"
#   Type    : span.tag-type
#   Desc    : div.abstract p
#   Pager   : ul.pagination a[href*="tx_solr%5Bpage%5D=N"]  (N=1-indexed)


class AnrScraper(BaseScraper):
    source_name = "ANR"
    base_url = f"{BASE}/fr/appels/"

    def fetch(self) -> list[dict]:
        items: list[dict] = []
        page = 0  # ANR uses 0-indexed tx_solr[page]; page 0 → no param

        while True:
            url = self.base_url if page == 0 else f"{self.base_url}?tx_solr%5Bpage%5D={page}"
            html = self._get(url)
            soup = self._soup(html)

            cards = soup.select("div.card.appel")
            if not cards:
                break

            for card in cards:
                title_tag = card.select_one("h2 a")
                date_tag = card.select_one("div.date")
                type_tag = card.select_one("span.tag-type")
                desc_tag = card.select_one("div.abstract p")

                if not title_tag:
                    continue

                # Normalize whitespace in the date block (multiline in source)
                date_raw = ""
                if date_tag:
                    date_raw = re.sub(r"\s+", " ", date_tag.get_text()).strip()

                items.append({
                    "titre": title_tag.get_text(strip=True),
                    "url": BASE + title_tag["href"],
                    "date_raw": date_raw,
                    "description": desc_tag.get_text(strip=True) if desc_tag else "",
                    "type": type_tag.get_text(strip=True) if type_tag else "",
                })

            next_page = soup.select_one(f'ul.pagination a[href*="tx_solr%5Bpage%5D={page + 1}"]')
            if not next_page:
                break
            page += 1

        return items

    def parse(self, html: str) -> list[dict]:
        # Parsing is done inline in fetch() for this scraper
        return []

    def normalize(self, raw: dict) -> AppelOffre:
        # Date field: "DD/MM/YYYY - DD/MM/YYYY" or "Mois YYYY - Mois YYYY"
        # Take the closing (last) date.
        date_raw = raw.get("date_raw", "")
        if " - " in date_raw:
            date_limite = normalize_date(date_raw.split(" - ")[-1].strip())
        else:
            date_limite = normalize_date(date_raw)

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
