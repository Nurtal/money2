import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://pro.inserm.fr"

# Real structure (verified 2026-04):
#   URL     : https://pro.inserm.fr/rubriques/appels-a-projets/aap
#   Articles: article.event_inserm
#   Title   : h2.entry-title
#   Date    : div.entry-content div.date  → "30.04.26"  (DD.MM.YY)
#   URL     : div.entry-content ul.links a  (first href)
#   Desc    : p.details
#   No pagination (consolidated page)

_DATE_DOT_RE = re.compile(r"(\d{1,2})\.(\d{2})\.(\d{2})$")


class InsermScraper(BaseScraper):
    source_name = "Inserm"
    base_url = f"{BASE}/rubriques/appels-a-projets/aap"

    def fetch(self) -> list[dict]:
        html = self._get(self.base_url)
        return self.parse(html)

    def parse(self, html: str) -> list[dict]:
        soup = self._soup(html)
        items = []

        for article in soup.select("article.event_inserm"):
            title_tag = article.select_one("h2.entry-title")
            if not title_tag:
                continue

            # Date in entry-content (skip the empty header date div)
            date_raw = ""
            content_div = article.select_one("div.entry-content")
            if content_div:
                date_div = content_div.select_one("div.date")
                if date_div:
                    # Strip prefix "Date limite :" if present
                    full_text = date_div.get_text(strip=True)
                    # Extract DD.MM.YY pattern
                    m = _DATE_DOT_RE.search(full_text)
                    if m:
                        date_raw = m.group(0)  # keep raw for normalize_date

            # URL: first link in ul.links
            url = self.base_url
            link_tag = article.select_one("ul.links a[href]")
            if link_tag:
                url = link_tag["href"]

            # Description
            desc_tag = article.select_one("p.details")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            items.append({
                "titre": title_tag.get_text(strip=True),
                "url": url,
                "date_raw": date_raw,
                "description": description,
            })

        return items

    def normalize(self, raw: dict) -> AppelOffre:
        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=_parse_inserm_date(raw.get("date_raw")),
            eligibilite=raw.get("description", ""),
            domaine="recherche biomédicale",
            mots_cles=["Inserm", "recherche"],
        )


def _parse_inserm_date(text: str | None):
    """Parse Inserm DD.MM.YY date format (e.g. '30.04.26' → 2026-04-30)."""
    if not text:
        return None
    m = _DATE_DOT_RE.search(text)
    if m:
        day, month, year_short = int(m.group(1)), int(m.group(2)), int(m.group(3))
        # Two-digit year: assume 2000s
        from datetime import date
        return date(2000 + year_short, month, day)
    # Fallback to generic parser
    return normalize_date(text)
