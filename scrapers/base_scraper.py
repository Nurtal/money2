import logging
import random
import time
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

from models.appel_offre import AppelOffre

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    source_name: str = ""
    base_url: str = ""

    def __init__(self, delay_min: float = 1.0, delay_max: float = 3.0, timeout: int = 30):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })

    def _get(self, url: str) -> str:
        """Fetch a URL with rate limiting. Returns HTML text."""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def _soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Retrieve raw data from the source. Returns list of raw dicts."""

    @abstractmethod
    def parse(self, html: str) -> list[dict]:
        """Parse HTML and extract raw field dicts."""

    @abstractmethod
    def normalize(self, raw: dict) -> AppelOffre:
        """Convert a raw dict into a validated AppelOffre."""

    def run(self) -> list[AppelOffre]:
        """Full pipeline: fetch → parse → normalize."""
        logger.info("Starting scraper: %s", self.source_name)
        try:
            raw_items = self.fetch()
            results = [self.normalize(item) for item in raw_items]
            logger.info("%s: %d items collected", self.source_name, len(results))
            return results
        except Exception:
            logger.exception("Scraper failed: %s", self.source_name)
            return []
