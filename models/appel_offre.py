from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class AppelOffre:
    titre: str
    source: str
    url_source: str
    date_scraping: datetime = field(default_factory=datetime.now)

    montant_min: float | None = None
    montant_max: float | None = None
    devise: str = "EUR"

    date_limite: date | None = None
    eligibilite: str = ""
    statut: str = "ouvert"  # "ouvert", "fermé", "à venir"
    domaine: str = ""
    mots_cles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "titre": self.titre,
            "source": self.source,
            "montant_min": self.montant_min,
            "montant_max": self.montant_max,
            "devise": self.devise,
            "date_limite": self.date_limite.isoformat() if self.date_limite else None,
            "eligibilite": self.eligibilite,
            "url_source": self.url_source,
            "date_scraping": self.date_scraping.isoformat(),
            "statut": self.statut,
            "domaine": self.domaine,
            "mots_cles": "|".join(self.mots_cles),
        }
