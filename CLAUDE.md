# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**HealthFundingScraper** is a Python 3.12 web scraper that aggregates French health sector funding opportunities (appels à projets/offres) from 35+ institutional sources (BPI France, ANR, INCa, ARS regions, foundations) into a unified CSV output.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Running

```bash
python run_all.py                              # Run all scrapers
python run_all.py --source bpi_france          # Run a specific scraper
python run_all.py --output ./output/my.csv     # Custom output path
python run_all.py --dry-run                    # No file writes
```

## Testing

```bash
pytest tests/                        # All tests
pytest tests/test_bpi.py             # Single test file
pytest tests/test_bpi.py::TestClass  # Single test
```

## Architecture

The project follows an abstract base + per-source scraper pattern:

**`scrapers/base_scraper.py`** — Abstract `BaseScraper` with three methods each scraper must implement:
- `fetch()` → raw HTTP/browser retrieval
- `parse(html)` → extract raw dicts from HTML
- `normalize(raw)` → return a validated `AppelOffre` instance

**`models/appel_offre.py`** — Shared `AppelOffre` dataclass/Pydantic model (titre, source, montant_min/max, date_limite, eligibilite, url_source, date_scraping, statut, domaine, mots_cles).

**`scrapers/`** — One file per source; ARS regional scrapers live in `scrapers/ars/`. Each inherits `BaseScraper` and sets `source_name` and `base_url` as class attributes.

**`utils/normalizer.py`** — Handles heterogeneous amount formats (`"jusqu'à 2M€"`, `"200 000 €"`) and date formats (`dd/mm/yyyy`, `mois YYYY`, ISO timestamps).

**`utils/deduplicator.py`** — Deduplicates by hashing titre + source.

**`utils/exporter.py`** — Exports to CSV (UTF-8 with BOM for Excel), JSON, or SQLite.

**`run_all.py`** — Orchestrates all scrapers in parallel and writes timestamped output to `output/appels_offres_sante_YYYYMMDD.csv`.

## Adding a New Scraper

1. Create `scrapers/<source_name>.py` inheriting from `BaseScraper`
2. Implement `fetch()`, `parse()`, `normalize()` returning `AppelOffre`
3. Add tests in `tests/test_<source_name>.py`
4. Document the source in `docs/source_mapping.md`
5. Register the scraper in `run_all.py`

Use `playwright` for JavaScript-heavy pages, `requests` + `beautifulsoup4` for static HTML, and `pdfplumber` for PDF announcements. Always add random delays between requests.

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `requests` / `beautifulsoup4` + `lxml` | Static page scraping |
| `playwright` | Dynamic (JS-rendered) pages |
| `pdfplumber` | PDF extraction |
| `pydantic` | `AppelOffre` schema validation |
| `pandas` | CSV export |
| `python-dotenv` | `.env` loading (API keys, proxy config) |
