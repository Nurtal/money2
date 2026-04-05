import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://www.fondation-arc.org"

# Real structure (verified 2026-04):
#   URL         : https://www.fondation-arc.org/appels-a-projets/
#   Featured    : div.c-highlighting  (1 per page)
#     Title     :   h2.h2
#     URL       :   a.c-button[href]
#   List cards  : li.c-cardProject.c-card
#     Title     :   div.h5
#     URL       :   a.c-buttonIcon[href]
#   Status      : div.c-cardProject__intro-title  (both card types)
#                 "Appel à projets ouvert" / "à venir" / "fermé"
#   Date        : div.c-cardProject__intro p strong  → "01 juin 2026"
#   Tags        : div.c-tags span
#   Pager       : a[href*="/page/{n}/"]

_STATUS_MAP = {
    "ouvert": "ouvert",
    "à venir": "à venir",
    "fermé": "fermé",
}
_DATE_RE = re.compile(r"Date de limite[^:]*:\s*", re.IGNORECASE)


def _parse_card(card, title_sel: str, url_sel: str) -> dict | None:
    title_tag = card.select_one(title_sel)
    url_tag = card.select_one(url_sel)
    if not title_tag or not url_tag:
        return None

    # Status
    statut_tag = card.select_one("div.c-cardProject__intro-title")
    statut_raw = statut_tag.get_text(strip=True).lower() if statut_tag else ""
    statut = "ouvert"
    for key, val in _STATUS_MAP.items():
        if key in statut_raw:
            statut = val
            break

    # Date: the <strong> inside c-cardProject__intro p
    date_raw = ""
    date_strong = card.select_one("div.c-cardProject__intro p strong")
    if date_strong:
        date_raw = date_strong.get_text(strip=True)

    # Tags
    tags = [s.get_text(strip=True) for s in card.select("div.c-tags span")]

    return {
        "titre": title_tag.get_text(strip=True),
        "url": url_tag["href"],
        "date_raw": date_raw,
        "statut": statut,
        "tags": tags,
    }


class FondationArcScraper(BaseScraper):
    source_name = "Fondation ARC"
    base_url = f"{BASE}/appels-a-projets/"

    def fetch(self) -> list[dict]:
        items: list[dict] = []
        page = 1

        while True:
            url = self.base_url if page == 1 else f"{self.base_url}page/{page}/"
            html = self._get(url)
            raw = self.parse(html)
            if not raw:
                break
            items.extend(raw)

            soup = self._soup(html)
            if not soup.select_one(f'a[href*="/page/{page + 1}/"]'):
                break
            page += 1

        return items

    def parse(self, html: str) -> list[dict]:
        soup = self._soup(html)
        items = []

        # Featured / highlighted card (first position)
        highlight = soup.select_one("div.c-highlighting")
        if highlight:
            r = _parse_card(highlight, "h2.h2, h2", "a.c-button[href]")
            if r:
                items.append(r)

        # Regular list cards
        for card in soup.select("li.c-cardProject.c-card"):
            r = _parse_card(card, "div.h5", "a.c-buttonIcon[href]")
            if r:
                items.append(r)

        return items

    def normalize(self, raw: dict) -> AppelOffre:
        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=normalize_date(raw.get("date_raw")),
            statut=raw.get("statut", "ouvert"),
            domaine="oncologie",
            mots_cles=["cancer", "cancérologie"] + raw.get("tags", []),
        )
