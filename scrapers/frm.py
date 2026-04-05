import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://www.frm.org"

# Real structure (verified 2026-04):
#   URL     : https://www.frm.org/fr/programmes  (single page, no pagination)
#   Items   : li.program details
#   Title   : summary h3  (or h3.Program_title__*)
#   Date    : p.Program_date__Ahfpg  → "Date de clôture : 23 avril 2026"
#   Status  : Program_disable__DkwF6 class on date tag  → fermé if present
#   Desc    : div.Program_description__j4nNH > p (first)
#   Tags    : li.Program_tag__kwMDn (first)
#   URL     : BASE/fr/programmes#{details_id}

_DATE_PREFIX_RE = re.compile(r"[Dd]ate de cl[oô]ture\s*:\s*(.+)", re.IGNORECASE)


class FrmScraper(BaseScraper):
    source_name = "FRM"
    base_url = f"{BASE}/fr/programmes"

    def fetch(self) -> list[dict]:
        html = self._get(self.base_url)
        return self.parse(html)

    def parse(self, html: str) -> list[dict]:
        soup = self._soup(html)
        items = []

        for details in soup.select("li.program details"):
            title_tag = details.select_one("summary h3")
            if not title_tag:
                continue

            # Build anchor URL from the details id attribute
            details_id = details.get("id", "")
            url = f"{self.base_url}#{details_id}" if details_id else self.base_url

            # Date and status
            date_raw = ""
            statut = "ouvert"
            date_tag = details.select_one("p.Program_date__Ahfpg")
            if date_tag:
                m = _DATE_PREFIX_RE.search(date_tag.get_text(strip=True))
                if m:
                    date_raw = m.group(1).strip()
                if "Program_disable__DkwF6" in (date_tag.get("class") or []):
                    statut = "fermé"

            # Description (first paragraph in the description div)
            description = ""
            desc_div = details.select_one("div.Program_description__j4nNH")
            if desc_div:
                p = desc_div.select_one("p")
                if p:
                    description = p.get_text(strip=True)

            # Category tag
            tag_items = details.select("li.Program_tag__kwMDn")
            categorie = tag_items[0].get_text(strip=True) if tag_items else ""

            items.append({
                "titre": title_tag.get_text(strip=True),
                "url": url,
                "date_raw": date_raw,
                "statut": statut,
                "description": description,
                "categorie": categorie,
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
            domaine="recherche médicale",
            mots_cles=["recherche médicale", raw.get("categorie", "")],
        )
