import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://www.cancer.fr"
_DATE_RE = re.compile(r"Date limite[^:]*:\s*(.+?)(?:\s*à\s*\d+[h:]\d+)?$", re.IGNORECASE)


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

        for li in soup.select("li"):
            title_tag = li.select_one("h3 a")
            if not title_tag:
                continue

            # Date and status are in <p> tags
            date_raw = ""
            statut = "ouvert"
            description = ""
            for p in li.select("p"):
                text = p.get_text(strip=True)
                m = _DATE_RE.search(text)
                if m:
                    date_raw = m.group(1).strip()
                elif text.lower() in ("en cours", "ouvert"):
                    statut = "ouvert"
                elif text.lower() in ("clos", "fermé", "clôturé"):
                    statut = "fermé"
                elif text.lower().startswith("résultat"):
                    statut = "fermé"
                else:
                    description = text

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
