import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://www.fondationdefrance.org"

# Real structure (verified 2026-04):
#   URL         : https://www.fondationdefrance.org/fr/appels-a-projets
#   Cards       : div[class~="uk-width-expand@m"]  (one per AAP)
#     Title     :   h3 > a  (relative href)
#     Date open :   div.uk-panel containing "Date d'ouverture"
#     Deadline  :   div.uk-panel containing "dépôt"  → "DD mois YYYY"
#     Desc      :   last div.uk-panel without date text
#   Filter      : only AAPs with health-related keywords are kept

_HEALTH_RE = re.compile(
    r"\b(?:santé|cancer|médi|neurolog|handicap|maladie|aidant|vieillissement"
    r"|alzheimer|neurodégénér|oncolog|thérapeutique|clinique|psychiatr|pharmac)\b",
    re.IGNORECASE,
)
_DEPOT_RE = re.compile(r"dépôt[^:]*:\s*(.+)", re.IGNORECASE)


class FondationDeFranceScraper(BaseScraper):
    source_name = "Fondation de France"
    base_url = f"{BASE}/fr/appels-a-projets"

    def fetch(self) -> list[dict]:
        html = self._get(self.base_url)
        return self.parse(html)

    def parse(self, html: str) -> list[dict]:
        soup = self._soup(html)
        items = []

        for card in soup.find_all("div", class_="uk-width-expand@m"):
            link_tag = card.select_one("h3 a")
            if not link_tag or not link_tag.get("href"):
                continue

            title = link_tag.get_text(strip=True)
            href = link_tag["href"]
            url = href if href.startswith("http") else BASE + href

            # Find deadline from the panel that mentions "dépôt"
            date_raw = ""
            description = ""
            for panel in card.select("div.uk-panel"):
                text = panel.get_text(separator=" ", strip=True)
                if not date_raw:
                    m = _DEPOT_RE.search(text)
                    if m:
                        date_raw = m.group(1).strip()
                        continue
                if "date" not in text.lower() and len(text) > 30:
                    description = text

            # Only keep health-related AAPs
            if not _HEALTH_RE.search(title + " " + description):
                continue

            items.append({
                "titre": title,
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
            date_limite=normalize_date(raw.get("date_raw")),
            eligibilite=raw.get("description", ""),
            domaine="santé / recherche médicale",
            mots_cles=_extract_keywords(raw.get("titre", "") + " " + raw.get("description", "")),
        )


def _extract_keywords(text: str) -> list[str]:
    keywords = []
    patterns = [
        (r"\bcancer\b", "cancer"),
        (r"\bneurodégénér|\bneurolog|\balzheimer", "neurodégénératif"),
        (r"\bhandicap\b", "handicap"),
        (r"\bsanté\b", "santé"),
        (r"\baidant", "aidants"),
        (r"\bvieillissement", "vieillissement"),
        (r"\boncolog", "oncologie"),
        (r"\bmédi", "médecine"),
        (r"\bmaladie", "maladies"),
    ]
    for pattern, kw in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            keywords.append(kw)
    return keywords
