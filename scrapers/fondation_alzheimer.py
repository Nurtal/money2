import re

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.normalizer import normalize_date

BASE = "https://www.fondation-alzheimer.org"

# Real structure (verified 2026-04):
#   Listing URL : https://www.fondation-alzheimer.org/je-suis-chercheur/financement-de-projets/
#   Programme links: a[href*="/financement-de-projets/<slug>/"]
#   Per sub-page:
#     Deadline  : text matching "limite de soumission : DD mois YYYY"
#     Title     : from the link text on the listing page

_PROG_PATH = "/je-suis-chercheur/financement-de-projets/"
_DEADLINE_RE = re.compile(
    r"limite de soumission\s*:\s*(\d{1,2}\s+\w+(?:\s+\d{4})?)",
    re.IGNORECASE,
)


class FondationAlzheimerScraper(BaseScraper):
    source_name = "Fondation Alzheimer"
    base_url = f"{BASE}{_PROG_PATH}"

    def fetch(self) -> list[dict]:
        listing_html = self._get(self.base_url)
        prog_links = self._parse_programme_links(listing_html)

        items = []
        for title, url in prog_links:
            sub_html = self._get(url)
            raw = self._parse_programme_page(title, url, sub_html)
            if raw:
                items.append(raw)
        return items

    def parse(self, html: str) -> list[dict]:
        """Return raw dicts for programme links found on the listing page."""
        links = self._parse_programme_links(html)
        return [{"titre": t, "url": u, "date_raw": ""} for t, u in links]

    def normalize(self, raw: dict) -> AppelOffre:
        return AppelOffre(
            titre=raw["titre"],
            source=self.source_name,
            url_source=raw["url"],
            date_limite=normalize_date(raw.get("date_raw")),
            domaine="neurodégénératif / Alzheimer",
            mots_cles=["Alzheimer", "maladies neurocognitives", "recherche"],
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _parse_programme_links(self, html: str) -> list[tuple[str, str]]:
        soup = self._soup(html)
        seen: set[str] = set()
        links: list[tuple[str, str]] = []
        for a in soup.select(f'a[href*="{_PROG_PATH}"]'):
            href = a["href"]
            # Normalise to absolute URL
            if not href.startswith("http"):
                href = BASE + href
            # Strip base URL to get path, skip the listing page itself
            path = href.replace(BASE, "")
            if path == _PROG_PATH or path in seen:
                continue
            seen.add(path)
            links.append((a.get_text(strip=True), href))
        return links

    def _parse_programme_page(self, title: str, url: str, html: str) -> dict | None:
        m = _DEADLINE_RE.search(html)
        date_raw = m.group(1).strip() if m else ""
        # Require at least a 4-digit year to avoid "5 mars" with no year
        if date_raw and not re.search(r"\d{4}", date_raw):
            date_raw = ""
        return {"titre": title, "url": url, "date_raw": date_raw}
