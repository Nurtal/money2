import hashlib

from models.appel_offre import AppelOffre


def _key(item: AppelOffre) -> str:
    raw = f"{item.source}|{item.titre}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()


def deduplicate(items: list[AppelOffre]) -> list[AppelOffre]:
    """Remove duplicates based on (source, titre) hash. Keeps first occurrence."""
    seen: set[str] = set()
    unique = []
    for item in items:
        k = _key(item)
        if k not in seen:
            seen.add(k)
            unique.append(item)
    return unique
