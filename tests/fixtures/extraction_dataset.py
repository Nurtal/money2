"""
Ground-truth dataset for extraction quality evaluation.

Each entry represents one realistic AAP as it would flow through a scraper's
normalize(raw) method.  The "expected" dict declares the ground-truth values
that normalize() must produce; only present keys are checked.

  date_limite       → exact match (datetime.date or None)
  montant_min/max   → exact match (float or None)
  statut            → exact match ("ouvert" | "fermé" | "à venir")
  domaine           → exact match (string)
  source            → exact match (string)
  mots_cles_include → subset check (all listed keywords must appear in mots_cles)

Run:
    pytest tests/test_extraction_quality.py -v          # per-case results
    pytest tests/test_extraction_quality.py -v -s       # + summary table
"""

from datetime import date

from scrapers.anr import AnrScraper
from scrapers.anrs import AnrsScraper
from scrapers.ars import ArsScraper
from scrapers.bpi_france import BpiFranceScraper
from scrapers.erc import ErcScraper
from scrapers.fondation_alzheimer import FondationAlzheimerScraper
from scrapers.fondation_arc import FondationArcScraper
from scrapers.fondation_de_france import FondationDeFranceScraper
from scrapers.frm import FrmScraper
from scrapers.horizon_europe import HorizonEuropeScraper
from scrapers.ihi import IhiScraper
from scrapers.inca import IncaScraper
from scrapers.inserm import InsermScraper

DATASET = [
    # ═══════════════════════════════════════════════════════════════════════════
    # ANR — Agence Nationale de la Recherche
    # Date format: "DD/MM/YYYY - DD/MM/YYYY" or "Mois YYYY - Mois YYYY"
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "anr-001",
        "description": "Date slash range: prend la 2e borne (clôture)",
        "scraper_cls": AnrScraper,
        "raw": {
            "titre": "AAP Santé Numérique et IA 2026",
            "url": "https://anr.fr/fr/detail/call/sante-ia-2026/",
            "date_raw": "02/04/2026 - 04/06/2026",
            "description": "Cet appel vise les projets de recherche en santé numérique.",
            "type": "Appel à projets spécifique",
        },
        "expected": {
            "source": "ANR",
            "date_limite": date(2026, 6, 4),
            "statut": "ouvert",
            "domaine": "recherche",
            "mots_cles_include": ["santé", "numérique"],
        },
    },
    {
        "id": "anr-002",
        "description": "Date mois-année range: mois de clôture → jour 1",
        "scraper_cls": AnrScraper,
        "raw": {
            "titre": "AAP Cancer et Biomarqueurs 2026",
            "url": "https://anr.fr/fr/detail/call/cancer-biomarqueurs/",
            "date_raw": "Janvier 2026 - Juin 2026",
            "description": "Financement de projets en oncologie.",
            "type": "Appel à projets spécifique",
        },
        "expected": {
            "source": "ANR",
            "date_limite": date(2026, 6, 1),
            "mots_cles_include": ["cancer"],
        },
    },
    {
        "id": "anr-003",
        "description": "Date absente → None, pas de montant",
        "scraper_cls": AnrScraper,
        "raw": {
            "titre": "AAP Neurosciences Cognitives 2026",
            "url": "https://anr.fr/fr/detail/call/neuro-2026/",
            "date_raw": "",
            "description": "",
            "type": "",
        },
        "expected": {
            "source": "ANR",
            "date_limite": None,
            "montant_min": None,
            "montant_max": None,
        },
    },
    {
        "id": "anr-004",
        "description": "Extraction mots-clés multi: santé + numérique + innovation",
        "scraper_cls": AnrScraper,
        "raw": {
            "titre": "AAP Innovation numérique en santé 2026",
            "url": "https://anr.fr/fr/detail/call/innovation-sante/",
            "date_raw": "01/03/2026 - 30/09/2026",
            "description": "Projets d'innovation numérique en santé.",
            "type": "Appel à projets générique",
        },
        "expected": {
            "date_limite": date(2026, 9, 30),
            "mots_cles_include": ["santé", "innovation", "numérique"],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # BPI France
    # Date format: "DD/MM/YYYY au DD/MM/YYYY"
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "bpi-001",
        "description": "Date 'DD/MM/YYYY au DD/MM/YYYY' → clôture",
        "scraper_cls": BpiFranceScraper,
        "raw": {
            "titre": "Appel à projets Santé Biomédicale 2026",
            "url": "https://www.bpifrance.fr/nos-appels-a-projets-concours/sante-biomedicale",
            "date_raw": "15/02/2026 au 30/06/2026",
            "description": "Financement de projets de recherche clinique en santé.",
            "categorie": "Santé",
        },
        "expected": {
            "source": "BPI France",
            "date_limite": date(2026, 6, 30),
            "domaine": "santé / innovation",
            "mots_cles_include": ["santé"],
        },
    },
    {
        "id": "bpi-002",
        "description": "Date seule sans borne d'ouverture",
        "scraper_cls": BpiFranceScraper,
        "raw": {
            "titre": "Concours i-Lab 2026 – Biotech et santé",
            "url": "https://www.bpifrance.fr/nos-appels-a-projets-concours/i-lab-2026",
            "date_raw": "15/09/2026",
            "description": "Innovation en biotechnologies.",
            "categorie": "Innovation",
        },
        "expected": {
            "source": "BPI France",
            "date_limite": date(2026, 9, 15),
        },
    },
    {
        "id": "bpi-003",
        "description": "Mots-clés composés: France 2030 + prévention + innovation + santé",
        "scraper_cls": BpiFranceScraper,
        "raw": {
            "titre": "France 2030 – Prévention et Innovation en santé",
            "url": "https://www.bpifrance.fr/nos-appels-a-projets-concours/france-2030-prevention",
            "date_raw": "01/04/2026 au 31/12/2026",
            "description": "Soutien aux projets de prévention.",
            "categorie": "Santé",
        },
        "expected": {
            "date_limite": date(2026, 12, 31),
            "mots_cles_include": ["santé", "innovation", "prévention", "France 2030"],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # INCa — Institut National du Cancer
    # Date format: ISO "YYYY-MM-DD" (from <time datetime>)
    # Statuts: "ouvert" | "fermé" (y compris "résultats")
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "inca-001",
        "description": "Date ISO, statut ouvert",
        "scraper_cls": IncaScraper,
        "raw": {
            "titre": "AAP Radiothérapie de précision 2026",
            "url": "https://www.cancer.fr/professionnels-de-la-recherche/appels-a-projets/rth26",
            "date_raw": "2026-05-27",
            "statut": "ouvert",
            "description": "Cet appel vise à réduire les séquelles de la radiothérapie.",
        },
        "expected": {
            "source": "INCa",
            "date_limite": date(2026, 5, 27),
            "statut": "ouvert",
            "domaine": "oncologie",
            "mots_cles_include": ["cancer"],
        },
    },
    {
        "id": "inca-002",
        "description": "Statut fermé transmis tel quel",
        "scraper_cls": IncaScraper,
        "raw": {
            "titre": "AAP Prévention Cancer 2025",
            "url": "https://www.cancer.fr/professionnels-de-la-recherche/appels-a-projets/prev25",
            "date_raw": "2025-04-15",
            "statut": "fermé",
            "description": "Prévention et dépistage précoce.",
        },
        "expected": {
            "date_limite": date(2025, 4, 15),
            "statut": "fermé",
        },
    },
    {
        "id": "inca-003",
        "description": "Date INCa fin d'année",
        "scraper_cls": IncaScraper,
        "raw": {
            "titre": "AAP Biomarqueurs tumoraux 2026",
            "url": "https://www.cancer.fr/professionnels-de-la-recherche/appels-a-projets/bio26",
            "date_raw": "2026-09-30",
            "statut": "ouvert",
            "description": "Recherche sur les biomarqueurs tumoraux.",
        },
        "expected": {
            "date_limite": date(2026, 9, 30),
            "statut": "ouvert",
        },
    },
    {
        "id": "inca-004",
        "description": "Date absente → None",
        "scraper_cls": IncaScraper,
        "raw": {
            "titre": "AAP Immunothérapie 2026",
            "url": "https://www.cancer.fr/professionnels-de-la-recherche/appels-a-projets/immuno26",
            "date_raw": "",
            "statut": "ouvert",
            "description": "",
        },
        "expected": {
            "date_limite": None,
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # FRM — Fondation pour la Recherche Médicale
    # Date format: "23 avril 2026" (texte complet après "Date de clôture :")
    # Statuts: via classe CSS Program_disable sur la balise date
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "frm-001",
        "description": "Date mois français complet + jour",
        "scraper_cls": FrmScraper,
        "raw": {
            "titre": "Grand Prix Scientifique FRM 2026",
            "url": "https://www.frm.org/fr/programmes#grand-prix-2026",
            "date_raw": "23 avril 2026",
            "statut": "ouvert",
            "description": "Prix annuel pour récompenser une découverte fondamentale.",
            "categorie": "Maladies cardiovasculaires",
        },
        "expected": {
            "source": "FRM",
            "date_limite": date(2026, 4, 23),
            "statut": "ouvert",
            "domaine": "recherche médicale",
        },
    },
    {
        "id": "frm-002",
        "description": "Statut fermé (classe disable présente)",
        "scraper_cls": FrmScraper,
        "raw": {
            "titre": "Financement équipe FRM 2025",
            "url": "https://www.frm.org/fr/programmes#equipe-2025",
            "date_raw": "30 novembre 2025",
            "statut": "fermé",
            "description": "Financement pluriannuel d'équipes de recherche.",
            "categorie": "Oncologie",
        },
        "expected": {
            "date_limite": date(2025, 11, 30),
            "statut": "fermé",
        },
    },
    {
        "id": "frm-003",
        "description": "Catégorie remontée dans mots_cles",
        "scraper_cls": FrmScraper,
        "raw": {
            "titre": "Bourse de Master FRM 2026",
            "url": "https://www.frm.org/fr/programmes#master-2026",
            "date_raw": "15 mai 2026",
            "statut": "ouvert",
            "description": "Bourse pour master 2 en neurosciences.",
            "categorie": "Maladies neurodégénératives",
        },
        "expected": {
            "date_limite": date(2026, 5, 15),
            "mots_cles_include": ["Maladies neurodégénératives"],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # Inserm
    # Date format spécifique: "DD.MM.YY" (ex: "30.04.26" → 2026-04-30)
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "inserm-001",
        "description": "Format DD.MM.YY (deux chiffres pour l'année)",
        "scraper_cls": InsermScraper,
        "raw": {
            "titre": "AAP MIE – Maladies infectieuses émergentes 2026",
            "url": "https://appels.inserm.fr/mie-2026",
            "date_raw": "30.04.26",
            "description": "Financement de projets sur les maladies infectieuses.",
        },
        "expected": {
            "source": "Inserm",
            "date_limite": date(2026, 4, 30),
            "domaine": "recherche biomédicale",
            "mots_cles_include": ["Inserm", "recherche"],
        },
    },
    {
        "id": "inserm-002",
        "description": "Date DD.MM.YY en janvier (mois 01)",
        "scraper_cls": InsermScraper,
        "raw": {
            "titre": "AAP Cancer Inserm 2026",
            "url": "https://appels.inserm.fr/cancer-2026",
            "date_raw": "15.01.26",
            "description": "",
        },
        "expected": {
            "date_limite": date(2026, 1, 15),
        },
    },
    {
        "id": "inserm-003",
        "description": "Date absente → None",
        "scraper_cls": InsermScraper,
        "raw": {
            "titre": "Programme Atip-Avenir 2026",
            "url": "https://pro.inserm.fr/rubriques/appels-a-projets/aap",
            "date_raw": "",
            "description": "Programme de soutien aux jeunes chercheurs.",
        },
        "expected": {
            "date_limite": None,
            "montant_min": None,
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # Fondation Alzheimer
    # Date format: "15 mars 2026" extrait par regex depuis la sous-page
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "alzheimer-001",
        "description": "Date française complète avec jour",
        "scraper_cls": FondationAlzheimerScraper,
        "raw": {
            "titre": "Programme Jeunes Chercheurs 2026",
            "url": "https://www.fondation-alzheimer.org/je-suis-chercheur/financement-de-projets/jeunes-chercheurs/",
            "date_raw": "15 mars 2026",
        },
        "expected": {
            "source": "Fondation Alzheimer",
            "date_limite": date(2026, 3, 15),
            "domaine": "neurodégénératif / Alzheimer",
            "mots_cles_include": ["Alzheimer", "recherche"],
        },
    },
    {
        "id": "alzheimer-002",
        "description": "Date absente (sous-page sans deadline explicite)",
        "scraper_cls": FondationAlzheimerScraper,
        "raw": {
            "titre": "Prix de recherche Alzheimer 2026",
            "url": "https://www.fondation-alzheimer.org/je-suis-chercheur/financement-de-projets/prix-recherche/",
            "date_raw": "",
        },
        "expected": {
            "date_limite": None,
            "mots_cles_include": ["Alzheimer", "maladies neurocognitives"],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # Fondation ARC pour la recherche sur le cancer
    # Date format: "01 juin 2026"
    # Statuts: "ouvert" | "à venir" | "fermé"
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "arc-001",
        "description": "Statut ouvert + tags inclus dans mots_cles",
        "scraper_cls": FondationArcScraper,
        "raw": {
            "titre": "AAP Labellisation Fondation ARC 2026",
            "url": "https://www.fondation-arc.org/appels-a-projets/labellisation-2026/",
            "date_raw": "01 juin 2026",
            "statut": "ouvert",
            "tags": ["cancer du sein", "cancer colorectal"],
        },
        "expected": {
            "source": "Fondation ARC",
            "date_limite": date(2026, 6, 1),
            "statut": "ouvert",
            "domaine": "oncologie",
            "mots_cles_include": ["cancer", "cancer du sein"],
        },
    },
    {
        "id": "arc-002",
        "description": "Statut à venir",
        "scraper_cls": FondationArcScraper,
        "raw": {
            "titre": "AAP Financement Équipes 2027",
            "url": "https://www.fondation-arc.org/appels-a-projets/equipes-2027/",
            "date_raw": "15 septembre 2026",
            "statut": "à venir",
            "tags": [],
        },
        "expected": {
            "date_limite": date(2026, 9, 15),
            "statut": "à venir",
        },
    },
    {
        "id": "arc-003",
        "description": "Statut fermé",
        "scraper_cls": FondationArcScraper,
        "raw": {
            "titre": "AAP Recherche Translationnelle 2025",
            "url": "https://www.fondation-arc.org/appels-a-projets/translationnelle-2025/",
            "date_raw": "30 novembre 2025",
            "statut": "fermé",
            "tags": ["immunothérapie"],
        },
        "expected": {
            "date_limite": date(2025, 11, 30),
            "statut": "fermé",
            "mots_cles_include": ["cancérologie", "immunothérapie"],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # Fondation de France
    # Date format: "15 juin 2026" (extrait du panel "dépôt")
    # Filtre santé activé sur titre + description
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "fdf-001",
        "description": "Date française + extraction mot-clé maladies neurodégénératives",
        "scraper_cls": FondationDeFranceScraper,
        "raw": {
            "titre": "Appel à projets maladies neurodégénératives 2026",
            "url": "https://www.fondationdefrance.org/fr/appels-a-projets/neurodegen-2026",
            "date_raw": "15 juin 2026",
            "description": "Soutien à la recherche sur la maladie d'Alzheimer et Parkinson.",
        },
        "expected": {
            "source": "Fondation de France",
            "date_limite": date(2026, 6, 15),
            "domaine": "santé / recherche médicale",
            "mots_cles_include": ["neurodégénératif", "maladies"],
        },
    },
    {
        "id": "fdf-002",
        "description": "Mots-clés: cancer + oncologie depuis titre et description",
        "scraper_cls": FondationDeFranceScraper,
        "raw": {
            "titre": "AAP Cancer et thérapeutiques innovantes",
            "url": "https://www.fondationdefrance.org/fr/appels-a-projets/cancer-2026",
            "date_raw": "30 avril 2026",
            "description": "Projets en oncologie ciblant les tumeurs solides.",
        },
        "expected": {
            "date_limite": date(2026, 4, 30),
            "mots_cles_include": ["cancer", "oncologie"],
        },
    },
    {
        "id": "fdf-003",
        "description": "Date absente (pas de deadline publiée)",
        "scraper_cls": FondationDeFranceScraper,
        "raw": {
            "titre": "Programme Aide aux aidants – santé",
            "url": "https://www.fondationdefrance.org/fr/appels-a-projets/aidants",
            "date_raw": "",
            "description": "Soutien aux aidants de personnes malades.",
        },
        "expected": {
            "date_limite": None,
            "mots_cles_include": ["aidants", "santé"],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # ANRS — Maladies infectieuses émergentes
    # Date format: texte français extrait après "Du X au Y" (ex: "25 mars 2026")
    # Statuts: "ouvert" | "fermé"
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "anrs-001",
        "description": "Date française (2e borne de 'Du X au Y')",
        "scraper_cls": AnrsScraper,
        "raw": {
            "titre": "AAP ANRS 2026 – Résistance aux antirétroviraux",
            "url": "https://anrs.fr/financements/appel/2026-antirétroviraux",
            "date_raw": "25 mars 2026",
            "statut": "ouvert",
        },
        "expected": {
            "source": "ANRS",
            "date_limite": date(2026, 3, 25),
            "statut": "ouvert",
            "domaine": "maladies infectieuses",
            "mots_cles_include": ["VIH", "hépatites"],
        },
    },
    {
        "id": "anrs-002",
        "description": "Statut fermé (tag 'Terminé')",
        "scraper_cls": AnrsScraper,
        "raw": {
            "titre": "AAP ANRS 2025 – Hépatites virales",
            "url": "https://anrs.fr/financements/appel/2025-hepatites",
            "date_raw": "30 septembre 2025",
            "statut": "fermé",
        },
        "expected": {
            "date_limite": date(2025, 9, 30),
            "statut": "fermé",
            "mots_cles_include": ["maladies infectieuses"],
        },
    },
    {
        "id": "anrs-003",
        "description": "Date mois seul (ouverture future sans jour)",
        "scraper_cls": AnrsScraper,
        "raw": {
            "titre": "AAP ANRS 2026 – COVID long",
            "url": "https://anrs.fr/financements/appel/2026-covid-long",
            "date_raw": "décembre 2026",
            "statut": "ouvert",
        },
        "expected": {
            "date_limite": date(2026, 12, 1),
            "statut": "ouvert",
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # ARS — Agences Régionales de Santé (12 régions)
    # Date format: "DD/MM/YYYY" extrait de "Clôture le DD/MM/YYYY"
    # source = nom de la région (ex: "ARS Île-de-France")
    # Statut: toujours "ouvert"
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "ars-001",
        "description": "Date slash, source région, statut toujours ouvert",
        "scraper_cls": ArsScraper,
        "raw": {
            "titre": "AAP Prévention addictions Île-de-France 2026",
            "url": "https://www.iledefrance.ars.sante.fr/appels-a-projets/prevention-addictions-2026",
            "date_raw": "30/06/2026",
            "description": "Soutien aux structures de prévention.",
            "source": "ARS Île-de-France",
        },
        "expected": {
            "source": "ARS Île-de-France",
            "date_limite": date(2026, 6, 30),
            "statut": "ouvert",
            "domaine": "santé / médico-social",
            "mots_cles_include": ["santé", "ARS"],
        },
    },
    {
        "id": "ars-002",
        "description": "Région Bretagne, date début d'année",
        "scraper_cls": ArsScraper,
        "raw": {
            "titre": "AAP Équipement EHPAD Bretagne 2026",
            "url": "https://www.bretagne.ars.sante.fr/appels-a-projets/ehpad-2026",
            "date_raw": "15/04/2026",
            "description": "Financement d'équipements pour les EHPAD.",
            "source": "ARS Bretagne",
        },
        "expected": {
            "source": "ARS Bretagne",
            "date_limite": date(2026, 4, 15),
            "statut": "ouvert",
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # Horizon Europe — EU Funding & Tenders Portal (API JSON)
    # Date format: ISO 8601 datetime "YYYY-MM-DDTHH:MM:SS"
    # Statuts: "ouvert" | "à venir" | "fermé" (mappés depuis "open"/"upcoming"/"closed")
    # Montants: budgetMin / budgetMax en euros (float)
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "horizon-001",
        "description": "ISO datetime + montants min/max + statut ouvert",
        "scraper_cls": HorizonEuropeScraper,
        "raw": {
            "titre": "Novel therapeutic approaches for rare diseases",
            "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/HORIZON-HLTH-2026-DISEASE-04-01",
            "date_raw": "2026-05-27T17:00:00",
            "statut": "ouvert",
            "description": "Innovative Health Research 2026",
            "montant_min": 3000000.0,
            "montant_max": 6000000.0,
        },
        "expected": {
            "source": "Horizon Europe",
            "date_limite": date(2026, 5, 27),
            "statut": "ouvert",
            "montant_min": 3000000.0,
            "montant_max": 6000000.0,
            "domaine": "recherche biomédicale",
            "mots_cles_include": ["Horizon Europe", "santé"],
        },
    },
    {
        "id": "horizon-002",
        "description": "Statut à venir (upcoming)",
        "scraper_cls": HorizonEuropeScraper,
        "raw": {
            "titre": "Immunotherapy combinations for solid tumours",
            "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/HORIZON-HLTH-2026-CANCER-01-01",
            "date_raw": "2026-09-15T17:00:00",
            "statut": "à venir",
            "description": "Cancer Missions 2026",
            "montant_min": None,
            "montant_max": 8000000.0,
        },
        "expected": {
            "date_limite": date(2026, 9, 15),
            "statut": "à venir",
            "montant_min": None,
            "montant_max": 8000000.0,
        },
    },
    {
        "id": "horizon-003",
        "description": "Statut fermé (closed)",
        "scraper_cls": HorizonEuropeScraper,
        "raw": {
            "titre": "Mental health in the digital age",
            "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/HORIZON-HLTH-2025-DISEASE-05-01",
            "date_raw": "2025-06-10T17:00:00",
            "statut": "fermé",
            "description": "Digital Mental Health 2025",
            "montant_min": None,
            "montant_max": None,
        },
        "expected": {
            "date_limite": date(2025, 6, 10),
            "statut": "fermé",
        },
    },
    {
        "id": "horizon-004",
        "description": "Sans montant → None",
        "scraper_cls": HorizonEuropeScraper,
        "raw": {
            "titre": "Microbiome and human health",
            "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/HORIZON-HLTH-2026-ENVHL-03-01",
            "date_raw": "2026-11-18T17:00:00",
            "statut": "ouvert",
            "description": "Health and Environment Cluster",
            "montant_min": None,
            "montant_max": None,
        },
        "expected": {
            "date_limite": date(2026, 11, 18),
            "montant_min": None,
            "montant_max": None,
            "statut": "ouvert",
        },
    },
    {
        "id": "horizon-005",
        "description": "Date absente → None",
        "scraper_cls": HorizonEuropeScraper,
        "raw": {
            "titre": "Pandemic preparedness networks",
            "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/HORIZON-HLTH-2026-IND-07",
            "date_raw": "",
            "statut": "ouvert",
            "description": "Global Health",
            "montant_min": None,
            "montant_max": None,
        },
        "expected": {
            "date_limite": None,
            "source": "Horizon Europe",
            "domaine": "recherche biomédicale",
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # ERC — European Research Council
    # Date format: ISO "YYYY-MM-DD" (depuis <time datetime>)
    # Statut: toujours "ouvert" (page liste uniquement les appels actifs)
    # Type de bourse détecté depuis le titre
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "erc-001",
        "description": "Starting Grant détecté depuis le titre",
        "scraper_cls": ErcScraper,
        "raw": {
            "titre": "ERC Starting Grants 2026 (ERC-2026-STG)",
            "url": "https://erc.europa.eu/apply-grant/open-calls/erc-2026-stg",
            "date_raw": "2026-10-08",
            "description": "Starting Grants support up-and-coming research leaders.",
        },
        "expected": {
            "source": "ERC",
            "date_limite": date(2026, 10, 8),
            "statut": "ouvert",
            "domaine": "recherche fondamentale",
            "mots_cles_include": ["ERC", "ERC Starting Grant"],
        },
    },
    {
        "id": "erc-002",
        "description": "Consolidator Grant détecté depuis le titre",
        "scraper_cls": ErcScraper,
        "raw": {
            "titre": "ERC Consolidator Grants 2026 (ERC-2026-COG)",
            "url": "https://erc.europa.eu/apply-grant/open-calls/erc-2026-cog",
            "date_raw": "2026-03-12",
            "description": "Consolidator Grants support researchers 7–12 years from PhD.",
        },
        "expected": {
            "date_limite": date(2026, 3, 12),
            "mots_cles_include": ["ERC Consolidator Grant"],
        },
    },
    {
        "id": "erc-003",
        "description": "Advanced Grant détecté depuis le titre",
        "scraper_cls": ErcScraper,
        "raw": {
            "titre": "ERC Advanced Grants 2026 (ERC-2026-ADG)",
            "url": "https://erc.europa.eu/apply-grant/open-calls/erc-2026-adg",
            "date_raw": "2026-08-28",
            "description": "Advanced Grants support established researchers.",
        },
        "expected": {
            "mots_cles_include": ["ERC Advanced Grant"],
            "statut": "ouvert",
        },
    },
    {
        "id": "erc-004",
        "description": "Proof of Concept détecté depuis le titre",
        "scraper_cls": ErcScraper,
        "raw": {
            "titre": "ERC Proof of Concept Grant 2026 (ERC-2026-PoC3)",
            "url": "https://erc.europa.eu/apply-grant/open-calls/erc-2026-poc3",
            "date_raw": "2026-05-06",
            "description": "PoC grants bridge research and market.",
        },
        "expected": {
            "date_limite": date(2026, 5, 6),
            "mots_cles_include": ["ERC Proof of Concept"],
        },
    },
    # ═══════════════════════════════════════════════════════════════════════════
    # IHI — Innovative Health Initiative (EU-industry partnership)
    # Date format: ISO "YYYY-MM-DD" (depuis <time datetime>)
    # Statuts: "ouvert" | "fermé" | "à venir"
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "ihi-001",
        "description": "ISO date, statut ouvert",
        "scraper_cls": IhiScraper,
        "raw": {
            "titre": "IHI Call 22 – AI-powered diagnostics",
            "url": "https://www.ihi.europa.eu/apply-funding/open-calls/ihi-2025-22",
            "date_raw": "2025-09-17",
            "statut": "ouvert",
            "description": "AI solutions for early disease detection.",
        },
        "expected": {
            "source": "IHI",
            "date_limite": date(2025, 9, 17),
            "statut": "ouvert",
            "domaine": "innovation santé",
            "mots_cles_include": ["IHI", "innovation santé"],
        },
    },
    {
        "id": "ihi-002",
        "description": "Statut à venir (upcoming)",
        "scraper_cls": IhiScraper,
        "raw": {
            "titre": "IHI Call 23 – Antimicrobial resistance",
            "url": "https://www.ihi.europa.eu/apply-funding/open-calls/ihi-2026-23",
            "date_raw": "2026-03-05",
            "statut": "à venir",
            "description": "New strategies against drug-resistant pathogens.",
        },
        "expected": {
            "date_limite": date(2026, 3, 5),
            "statut": "à venir",
        },
    },
    {
        "id": "ihi-003",
        "description": "Statut fermé",
        "scraper_cls": IhiScraper,
        "raw": {
            "titre": "IHI Call 20 – Rare diseases therapies",
            "url": "https://www.ihi.europa.eu/apply-funding/open-calls/ihi-2024-20",
            "date_raw": "2024-11-14",
            "statut": "fermé",
            "description": "Innovative therapies for rare diseases.",
        },
        "expected": {
            "date_limite": date(2024, 11, 14),
            "statut": "fermé",
        },
    },
    {
        "id": "ihi-004",
        "description": "Date absente + mots-clés fixes",
        "scraper_cls": IhiScraper,
        "raw": {
            "titre": "IHI Call 24 – Digital health tools",
            "url": "https://www.ihi.europa.eu/apply-funding/open-calls/ihi-2026-24",
            "date_raw": "",
            "statut": "ouvert",
            "description": "",
        },
        "expected": {
            "date_limite": None,
            "mots_cles_include": ["IHI", "partenariat européen"],
        },
    },
]
