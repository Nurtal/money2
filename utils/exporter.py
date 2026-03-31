import json
import sqlite3
from pathlib import Path

import pandas as pd

from models.appel_offre import AppelOffre


def to_csv(items: list[AppelOffre], path: str | Path) -> None:
    """Export to UTF-8 with BOM CSV (Excel-compatible)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([item.to_dict() for item in items])
    df.to_csv(path, index=False, encoding="utf-8-sig")


def to_json(items: list[AppelOffre], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([item.to_dict() for item in items], f, ensure_ascii=False, indent=2)


def to_sqlite(items: list[AppelOffre], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([item.to_dict() for item in items])
    with sqlite3.connect(path) as conn:
        df.to_sql("appels_offres", conn, if_exists="replace", index=False)
