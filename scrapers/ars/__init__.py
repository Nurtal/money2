import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

# Real structure (verified 2026-04) — identical Drupal theme across all ARS regions:
#   Cards       : div.accueil-appels-projets--item
#     Title     :   h3 > a  (relative href)
#     Type      :   div.accueil-appels-projets--item--type-appel p
#     Description:  div.accueil-appels-projets--item--description p
#     Date      :   div.accueil-appels-projets--item--infos p  → "Clôture le DD/MM/YYYY"
#
# ARS regions verified to use this structure (2026-04):
#   Grand Est, Bretagne, Auvergne-RA, Normandie, Hauts-de-France,
#   Bourgogne-FC, Île-de-France, Nouvelle-Aquitaine, Occitanie, PACA,
#   Pays-de-Loire, Corse

_DATE_RE = re.compile(r"(\d{1,2}/\d{2}/\d{4})")

# Map: short region key → (display name, base URL)
ARS_REGIONS: dict[str, tuple[str, str]] = {
    "grand_est": ("ARS Grand Est", "https://www.grand-est.ars.sante.fr"),
    "bretagne": ("ARS Bretagne", "https://www.bretagne.ars.sante.fr"),
    "auvergne_ra": ("ARS Auvergne-Rhône-Alpes", "https://www.auvergne-rhone-alpes.ars.sante.fr"),
    "normandie": ("ARS Normandie", "https://www.normandie.ars.sante.fr"),
    "hauts_de_france": ("ARS Hauts-de-France", "https://www.hauts-de-france.ars.sante.fr"),
    "bourgogne_fc": ("ARS Bourgogne-Franche-Comté", "https://www.bourgogne-franche-comte.ars.sante.fr"),
    "ile_de_france": ("ARS Île-de-France", "https://www.iledefrance.ars.sante.fr"),
    "nouvelle_aquitaine": ("ARS Nouvelle-Aquitaine", "https://www.nouvelle-aquitaine.ars.sante.fr"),
    "occitanie": ("ARS Occitanie", "https://www.occitanie.ars.sante.fr"),
    "paca": ("ARS PACA", "https://www.paca.ars.sante.fr"),
    "pays_de_loire": ("ARS Pays-de-Loire", "https://www.pays-de-la-loire.ars.sante.fr"),
    "corse": ("ARS Corse", "https://www.corse.ars.sante.fr"),
}


class ArsScraper(BaseScraper):
    """Scrapes all ARS regional homepage AAP listings in one pass."""

    source_name = "ARS"
    base_url = "https://www.grand-est.ars.sante.fr"  # representative; not used in fetch()

    def fetch(self) -> list[dict]:
        items: list[dict] = []
        for region_key, (region_name, region_base) in ARS_REGIONS.items():
            try:
                html = self._get(region_base + "/")
                region_items = self._parse_region(html, region_name, region_base)
                items.extend(region_items)
            except Exception:
                pass
        return items

    def parse(self, html: str) -> list[dict]:
        """Parse a single ARS region homepage."""
        return self._parse_region(html, self.source_name, self.base_url)

    def normalize(self, raw: dict) -> AppelOffre:
        return AppelOffre(
            titre=raw["titre"],
            source=raw.get("source", self.source_name),
            url_source=raw["url"],
            date_limite=normalize_date(raw.get("date_raw")),
            eligibilite=raw.get("description", ""),
            statut="ouvert",
            domaine="santé / médico-social",
            mots_cles=["santé", "ARS", "appel à projets"],
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _parse_region(self, html: str, region_name: str, base: str) -> list[dict]:
        soup = self._soup(html)
        items = []
        for card in soup.select("div.accueil-appels-projets--item"):
            link_tag = card.select_one("h3 a")
            if not link_tag:
                continue

            href = link_tag.get("href", "")
            url = href if href.startswith("http") else base + href

            # Date: "Clôture le DD/MM/YYYY"
            date_raw = ""
            info_p = card.select_one("div.accueil-appels-projets--item--infos p")
            if info_p:
                m = _DATE_RE.search(info_p.get_text(strip=True))
                if m:
                    date_raw = m.group(1)

            desc_p = card.select_one("div.accueil-appels-projets--item--description p")

            items.append({
                "titre": link_tag.get_text(strip=True),
                "url": url,
                "date_raw": date_raw,
                "description": desc_p.get_text(strip=True) if desc_p else "",
                "source": region_name,
            })
        return items
