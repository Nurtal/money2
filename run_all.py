#!/usr/bin/env python3
"""
Main orchestrator — runs all registered scrapers and exports results.

Usage:
    python run_all.py
    python run_all.py --source bpi_france
    python run_all.py --output ./output/my_export.csv
    python run_all.py --dry-run
"""

import argparse
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from models.appel_offre import AppelOffre
from scrapers.base_scraper import BaseScraper
from utils.deduplicator import deduplicate
from utils.exporter import to_csv

load_dotenv()

# ── Logging setup ────────────────────────────────────────────────────────────
log_file = os.getenv("LOG_FILE", "logs/scraper.log")
Path(log_file).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── Scraper registry ─────────────────────────────────────────────────────────
# Import and register scrapers here as they are implemented:
# from scrapers.bpi_france import BpiFranceScraper
# from scrapers.anr import AnrScraper

SCRAPERS: dict[str, type[BaseScraper]] = {
    # "bpi_france": BpiFranceScraper,
    # "anr": AnrScraper,
}


def run_scraper(scraper_cls: type[BaseScraper]) -> list[AppelOffre]:
    delay_min = float(os.getenv("REQUEST_DELAY_MIN", "1.0"))
    delay_max = float(os.getenv("REQUEST_DELAY_MAX", "3.0"))
    timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
    return scraper_cls(delay_min=delay_min, delay_max=delay_max, timeout=timeout).run()


def main() -> None:
    parser = argparse.ArgumentParser(description="HealthFundingScraper — run all scrapers")
    parser.add_argument("--source", help="Run a single scraper by key (e.g. bpi_france)")
    parser.add_argument("--output", help="Output CSV path (default: output/appels_offres_YYYYMMDD.csv)")
    parser.add_argument("--dry-run", action="store_true", help="Run scrapers but skip writing output")
    args = parser.parse_args()

    # Select scrapers to run
    if args.source:
        if args.source not in SCRAPERS:
            logger.error("Unknown source '%s'. Available: %s", args.source, list(SCRAPERS))
            raise SystemExit(1)
        targets = {args.source: SCRAPERS[args.source]}
    else:
        targets = SCRAPERS

    if not targets:
        logger.warning("No scrapers registered yet. Add scrapers to SCRAPERS in run_all.py.")
        return

    # Run in parallel
    all_items: list[AppelOffre] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_scraper, cls): name for name, cls in targets.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                items = future.result()
                all_items.extend(items)
                logger.info("%-20s → %d items", name, len(items))
            except Exception:
                logger.exception("Scraper '%s' raised an exception", name)

    all_items = deduplicate(all_items)
    logger.info("Total after deduplication: %d items", len(all_items))

    if args.dry_run:
        logger.info("Dry-run mode — skipping export.")
        return

    output_dir = os.getenv("OUTPUT_DIR", "output/")
    datestamp = datetime.now().strftime("%Y%m%d")
    output_path = args.output or str(Path(output_dir) / f"appels_offres_sante_{datestamp}.csv")

    to_csv(all_items, output_path)
    logger.info("Exported to %s", output_path)


if __name__ == "__main__":
    main()
