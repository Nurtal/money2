from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://www.ihi.europa.eu"

# Approximate structure (IHI website, Drupal CMS, verified 2026-04):
#   URL      : https://www.ihi.europa.eu/apply-funding/open-calls
#   Articles : article.call  or  article.node--type-call  or  div.call-item
#   Title    : h2 a  or  h3 a  (relative href → prepend BASE)
#   Date     : time[datetime]  → ISO "YYYY-MM-DD"
#   Status   : span.status | div.status | .field--name-field-status
#              "Open" | "Closed" | "Upcoming"
#   Desc     : div.description p  or  div.field--name-body p

_STATUS_MAP = {
    "open": "ouvert",
    "closed": "fermé",
    "upcoming": "à venir",
    "forthcoming": "à venir",
}


class IhiScraper(BaseScraper):
    source_name = "IHI"
    base_url = f"{BASE}/apply-funding/open-calls"

    def fetch(self) -> list[dict]:
        html = self._get(self.base_url)
        return self.parse(html)

    def parse(self, html: str) -> list[dict]:
        soup = self._soup(html)
        items = []

        for article in soup.select("article.call, article.node--type-call, div.call-item"):
            title_tag = article.select_one("h2 a, h3 a, h4 a")
            if not title_tag:
                continue

            date_raw = ""
            time_tag = article.select_one("time[datetime]")
            if time_tag:
                date_raw = time_tag["datetime"][:10]

            statut = "ouvert"
            status_tag = article.select_one(
                "span.status, div.status, .field--name-field-status"
            )
            if status_tag:
                st = status_tag.get_text(strip=True).lower()
                statut = _STATUS_MAP.get(st, "ouvert")

            desc_tag = article.select_one(
                "div.description p, div.field--name-body p, p.summary"
            )
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            href = title_tag.get("href", "")
            url = href if href.startswith("http") else BASE + href

            items.append({
                "titre": title_tag.get_text(strip=True),
                "url": url,
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
            domaine="innovation santé",
            mots_cles=["IHI", "innovation santé", "partenariat européen"],
        )
