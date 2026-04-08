from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://erc.europa.eu"

# Approximate structure (ERC website, Drupal CMS, verified 2026-04):
#   URL    : https://erc.europa.eu/apply-grant/open-calls
#   Rows   : article.views-row  or  div.views-row
#   Title  : h3.node__title a  (relative href → prepend BASE)
#   Date   : time[datetime]    → ISO "YYYY-MM-DDThh:mm:ss+TZ"
#   Desc   : div.field--name-body p  or  div.field-items p

_GRANT_TYPES = {
    "starting": "ERC Starting Grant",
    "consolidator": "ERC Consolidator Grant",
    "advanced": "ERC Advanced Grant",
    "synergy": "ERC Synergy Grant",
    "proof of concept": "ERC Proof of Concept",
}


class ErcScraper(BaseScraper):
    source_name = "ERC"
    base_url = f"{BASE}/apply-grant/open-calls"

    def fetch(self) -> list[dict]:
        html = self._get(self.base_url)
        return self.parse(html)

    def parse(self, html: str) -> list[dict]:
        soup = self._soup(html)
        items = []

        for row in soup.select("article.views-row, div.views-row"):
            title_tag = row.select_one("h3.node__title a, h2.node__title a, h3 a, h2 a")
            if not title_tag:
                continue

            time_tag = row.select_one("time[datetime]")
            date_raw = time_tag["datetime"][:10] if time_tag else ""

            desc_tag = row.select_one("div.field--name-body p, div.field-items p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            href = title_tag.get("href", "")
            url = href if href.startswith("http") else BASE + href

            items.append({
                "titre": title_tag.get_text(strip=True),
                "url": url,
                "date_raw": date_raw,
                "description": description,
            })

        return items

    def normalize(self, raw: dict) -> AppelOffre:
        titre_lower = raw["titre"].lower()
        grant_type = next(
            (v for k, v in _GRANT_TYPES.items() if k in titre_lower),
            "ERC Grant",
        )

        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=normalize_date(raw.get("date_raw")),
            eligibilite=raw.get("description", ""),
            statut="ouvert",
            domaine="recherche fondamentale",
            mots_cles=["ERC", grant_type],
        )
