import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://www.bpifrance.fr"

# Real structure (verified 2026-04):
#   URL     : https://www.bpifrance.fr/nos-appels-a-projets-concours?labels=267
#             label 267 = Santé
#   Cards   : div.article-card.card-our-project
#   Title   : h3 a  (relative href → prepend BASE)
#   Date    : span.card-date  → "DD/MM/YYYY au DD/MM/YYYY"
#   Desc    : div.desc p (first)
#   Category: span.rubrique
#   Pager   : li.pager__item a (href contains "?page=N")


class BpiFranceScraper(BaseScraper):
    source_name = "BPI France"
    base_url = f"{BASE}/nos-appels-a-projets-concours"
    _sante_label = "267"  # Santé theme label id

    def fetch(self) -> list[dict]:
        items: list[dict] = []
        page = 0  # Drupal uses 0-indexed pages

        while True:
            params = f"?labels={self._sante_label}"
            if page > 0:
                params += f"&page={page}"
            html = self._get(f"{self.base_url}{params}")
            soup = self._soup(html)

            cards = soup.select("div.article-card.card-our-project")
            if not cards:
                break

            for card in cards:
                title_tag = card.select_one("h3 a")
                date_tag = card.select_one("span.card-date")
                desc_tag = card.select_one("div.desc p")
                cat_tag = card.select_one("span.rubrique")

                if not title_tag:
                    continue

                href = title_tag.get("href", "")
                url = href if href.startswith("http") else BASE + href

                items.append({
                    "titre": title_tag.get_text(strip=True),
                    "url": url,
                    "date_raw": date_tag.get_text(strip=True) if date_tag else "",
                    "description": desc_tag.get_text(strip=True) if desc_tag else "",
                    "categorie": cat_tag.get_text(strip=True) if cat_tag else "",
                })

            # Pagination: Drupal pager links like href="?page=1"
            next_link = soup.select_one(f'li.pager__item a[href*="page={page + 1}"]')
            if not next_link:
                break
            page += 1

        return items

    def parse(self, html: str) -> list[dict]:
        return []

    def normalize(self, raw: dict) -> AppelOffre:
        # Date: "DD/MM/YYYY au DD/MM/YYYY" → take closing date (second part)
        date_raw = raw.get("date_raw", "")
        if " au " in date_raw:
            date_limite = normalize_date(date_raw.split(" au ")[-1].strip())
        else:
            date_limite = normalize_date(date_raw)

        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=date_limite,
            eligibilite=raw.get("description", ""),
            domaine="santé / innovation",
            mots_cles=_extract_keywords(raw.get("titre", "") + " " + raw.get("description", "")),
        )


def _extract_keywords(text: str) -> list[str]:
    keywords = []
    patterns = [
        (r"\bsanté\b", "santé"),
        (r"\bcancer\b", "cancer"),
        (r"\bnumérique\b", "numérique"),
        (r"\binnovation\b", "innovation"),
        (r"\bbiothérapie", "biothérapie"),
        (r"\bprévention\b", "prévention"),
        (r"\bFrance\s*2030\b", "France 2030"),
    ]
    for pattern, kw in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            keywords.append(kw)
    return keywords
