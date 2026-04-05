import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://anrs.fr"

# Real structure (verified 2026-04):
#   URL     : https://anrs.fr/financements/tous-les-appels-a-projets/
#   Cards   : div.card-free
#   Title   : h2 a  (absolute URL, no BASE prefix needed)
#   Date    : .card-free__footer p  → "Du 16 février 2026 au 25 mars 2026"
#   Status  : span.tag--primary span  → "Terminé", "En cours"
#   Pager   : a[href*="/page/{n}/"]

_DATES_RE = re.compile(r"[Dd]u\s+(.+?)\s+au\s+(.+)$")


class AnrsScraper(BaseScraper):
    source_name = "ANRS"
    base_url = f"{BASE}/financements/tous-les-appels-a-projets/"

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

        for card in soup.select("div.card-free"):
            title_tag = card.select_one("h2 a")
            if not title_tag:
                continue

            titre = title_tag.get_text(strip=True)
            url = title_tag["href"]  # already absolute

            # Closing date from footer paragraph "Du … au …"
            date_raw = ""
            footer_p = card.select_one(".card-free__footer p")
            if footer_p:
                m = _DATES_RE.search(footer_p.get_text(strip=True))
                if m:
                    date_raw = m.group(2).strip()

            # Status from tag badge
            statut = "ouvert"
            for tag_span in card.select("span.tag span"):
                txt = tag_span.get_text(strip=True).lower()
                if txt in ("terminé", "clos", "fermé"):
                    statut = "fermé"
                elif txt in ("en cours", "ouvert"):
                    statut = "ouvert"

            items.append({
                "titre": titre,
                "url": url,
                "date_raw": date_raw,
                "statut": statut,
            })

        return items

    def normalize(self, raw: dict) -> AppelOffre:
        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=normalize_date(raw.get("date_raw")),
            statut=raw.get("statut", "ouvert"),
            domaine="maladies infectieuses",
            mots_cles=["VIH", "hépatites", "maladies infectieuses"],
        )
