import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://anrs.fr"
_DATES_RE = re.compile(r"[Dd]u\s+(.+?)\s+au\s+(.+?)$")
_OPEN_RE = re.compile(r"[Dd]ates?\s+d.ouverture\s*:\s*(.+?)\s*-\s*(.+?)$")


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

        # Cards: anchor tags containing a <strong> title that link to the detail page
        for a_tag in soup.find_all("a", href=re.compile(r"/financements/tous-les-appels-a-projets/.+")):
            strong = a_tag.find("strong")
            if not strong:
                continue

            titre = strong.get_text(strip=True)
            url = a_tag["href"]

            # Walk up to the card container to find dates and status
            card = a_tag.parent
            for _ in range(4):  # walk up a few levels
                if card is None:
                    break
                texts = [p.get_text(strip=True) for p in card.find_all("p")]
                if texts:
                    break
                card = card.parent

            date_raw = ""
            statut = "ouvert"
            if card:
                for text in [p.get_text(strip=True) for p in card.find_all("p")]:
                    m = _DATES_RE.search(text)
                    if m:
                        date_raw = m.group(2).strip()
                        continue
                    m2 = _OPEN_RE.search(text)
                    if m2:
                        date_raw = m2.group(2).strip()

                for div in card.find_all("div"):
                    txt = div.get_text(strip=True).lower()
                    if "terminé" in txt or "clos" in txt or "fermé" in txt:
                        statut = "fermé"
                    elif "en cours" in txt or "ouvert" in txt:
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
