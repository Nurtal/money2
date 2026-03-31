# 🏥 HealthFundingScraper

> Agrégateur automatisé d'appels d'offres et de financements dans le domaine de la santé en France

---

## 📋 Description

**HealthFundingScraper** est un outil de scraping et de structuration automatique des appels à projets et financements publics dans le domaine de la santé en France. Il consolide en un seul fichier CSV les opportunités de financement issues de multiples sources institutionnelles (ARS, BPI France, ANR, INCa, Ligue contre le Cancer, etc.), permettant aux acteurs de la santé — chercheurs, associations, startups, établissements hospitaliers — d'identifier rapidement les appels pertinents.

### Exemple de sortie (`appels_offres_sante.csv`)

| titre | source | montant | date_limite | eligibilite |
|-------|--------|---------|-------------|-------------|
| AMI Santé Numérique 2025 | BPI France | 2 000 000 € | 30/06/2025 | PME, ETI, structures de soins |
| AAP Prévention cancer colorectal | INCa | 300 000 € | 15/04/2025 | Équipes de recherche publique |
| PRSE Occitanie – Environnement & Santé | ARS Occitanie | 150 000 € | 01/05/2025 | Associations, collectivités |

---

## 🗂️ Sources couvertes

### Institutionnelles nationales
| Source | Type | URL |
|--------|------|-----|
| **BPI France** | Aides à l'innovation, prêts, subventions | https://www.bpifrance.fr/nos-appels-a-projets-concours |
| **ANR** (Agence Nationale de la Recherche) | Financements recherche fondamentale & appliquée | https://anr.fr/fr/appels-ouverts/ |
| **INCa** (Institut National du Cancer) | Recherche en cancérologie | https://www.e-cancer.fr/Professionnels-de-sante/Les-appels-a-projets |
| **ANRS** (Maladies infectieuses émergentes) | VIH, hépatites, Covid, émergences | https://www.anrs.fr/fr/appels-a-projets |
| **Inserm** | Recherche biomédicale | https://www.inserm.fr/recherche-inserm/financements/ |
| **FRM** (Fondation pour la Recherche Médicale) | Subventions chercheurs, équipes | https://www.frm.org/chercheurs/appels-a-projets |
| **CNRS** | Projets interdisciplinaires santé | https://www.cnrs.fr/fr/cnrs-appels-a-projets |
| **Agence du Numérique en Santé (ANS)** | E-santé, interopérabilité | https://esante.gouv.fr/appels-a-projets |
| **SGPI / France 2030** | Grands défis industriels & santé | https://www.gouvernement.fr/france-2030 |

### ARS (Agences Régionales de Santé) — 18 régions
| ARS | URL |
|-----|-----|
| ARS Île-de-France | https://www.iledefrance.ars.sante.fr |
| ARS Auvergne-Rhône-Alpes | https://www.auvergne-rhone-alpes.ars.sante.fr |
| ARS Nouvelle-Aquitaine | https://www.nouvelle-aquitaine.ars.sante.fr |
| ARS Occitanie | https://www.occitanie.ars.sante.fr |
| ARS Provence-Alpes-Côte d'Azur | https://www.paca.ars.sante.fr |
| ARS Hauts-de-France | https://www.hauts-de-france.ars.sante.fr |
| ARS Grand Est | https://www.grand-est.ars.sante.fr |
| ARS Normandie | https://www.normandie.ars.sante.fr |
| ARS Bretagne | https://www.bretagne.ars.sante.fr |
| ARS Pays de la Loire | https://www.pays-de-la-loire.ars.sante.fr |
| ARS Centre-Val de Loire | https://www.centre-val-de-loire.ars.sante.fr |
| ARS Bourgogne-Franche-Comté | https://www.bourgogne-franche-comte.ars.sante.fr |
| ARS Corse | https://www.corse.ars.sante.fr |
| ARS La Réunion | https://www.lareunion.ars.sante.fr |
| ARS Martinique | https://www.martinique.ars.sante.fr |
| ARS Guadeloupe | https://www.guadeloupe.ars.sante.fr |
| ARS Guyane | https://www.guyane.ars.sante.fr |
| ARS Mayotte | https://www.mayotte.ars.sante.fr |

### Fondations & associations
| Source | Domaine |
|--------|---------|
| **Ligue contre le Cancer** | Oncologie, soutien à la recherche | 
| **Fondation ARC** | Recherche contre le cancer |
| **AFM-Téléthon** | Maladies neuromusculaires |
| **Fondation de France** | Santé, vieillissement, handicap |
| **Fondation Alzheimer** | Maladies neurodégénératives |
| **Sidaction** | VIH/SIDA |
| **Fondation du Souffle** | Pneumologie |
| **Fondation Roche** | Innovation thérapeutique |

---

## 🚀 Étapes de réalisation

### Phase 1 — Mise en place de l'environnement *(~1 semaine)*

- [ ] Initialiser le projet Python avec un environnement virtuel (`venv` ou `conda`)
- [ ] Créer la structure de dossiers du projet (voir section **Structure du projet**)
- [ ] Installer les dépendances principales : `requests`, `beautifulsoup4`, `scrapy` ou `selenium`, `pandas`, `lxml`, `playwright`
- [ ] Configurer un fichier `.env` pour les éventuelles clés d'API et proxies
- [ ] Mettre en place le `requirements.txt` et le `pyproject.toml`

```bash
git clone https://github.com/votre-user/HealthFundingScraper.git
cd HealthFundingScraper
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

---

### Phase 2 — Analyse et cartographie des sources *(~1 semaine)*

- [ ] Auditer chaque site source : structure HTML, pagination, contenu dynamique (JavaScript), présence d'une API ou flux RSS
- [ ] Identifier pour chaque source :
  - Le sélecteur CSS / XPath de chaque champ cible (titre, montant, date, éligibilité)
  - Le type de scraping requis : statique (BS4), dynamique (Playwright/Selenium), ou API REST
  - La fréquence de mise à jour du site
- [ ] Documenter les résultats dans `/docs/source_mapping.md`
- [ ] Prioriser les sources par richesse de données et facilité d'accès

---

### Phase 3 — Développement des scrapers *(~3 semaines)*

- [ ] Créer un scraper de base abstrait (`BaseScraper`) avec les méthodes communes : `fetch()`, `parse()`, `normalize()`
- [ ] Implémenter un scraper dédié par source (un fichier par source dans `/scrapers/`)
- [ ] Gérer les cas particuliers :
  - Sites avec CAPTCHA → rotation de user-agents + délais aléatoires
  - Contenu chargé en JavaScript → utilisation de Playwright
  - PDFs annonçant les AAP → extraction via `pdfplumber` ou `PyMuPDF`
- [ ] Normaliser les montants (formats variés : `"jusqu'à 2M€"`, `"200 000 €"`, etc.)
- [ ] Normaliser les dates (formats `dd/mm/yyyy`, `mois YYYY`, timestamps ISO)
- [ ] Écrire des tests unitaires pour chaque scraper (`/tests/`)

```python
# Exemple de structure d'un scraper
class ARSIleDeFranceScraper(BaseScraper):
    source_name = "ARS Île-de-France"
    base_url = "https://www.iledefrance.ars.sante.fr/appels-a-projets"

    def fetch(self) -> list[dict]:
        ...

    def parse(self, html: str) -> list[dict]:
        ...

    def normalize(self, raw: dict) -> AppelOffre:
        ...
```

---

### Phase 4 — Structuration et export des données *(~1 semaine)*

- [ ] Définir le schéma de données standardisé (dataclass ou Pydantic model) :

```python
@dataclass
class AppelOffre:
    titre: str
    source: str
    montant_min: float | None
    montant_max: float | None
    devise: str  # EUR par défaut
    date_limite: date | None
    eligibilite: str
    url_source: str
    date_scraping: datetime
    statut: str  # "ouvert", "fermé", "à venir"
    domaine: str  # "oncologie", "numérique", "prévention"...
    mots_cles: list[str]
```

- [ ] Implémenter la déduplication par hachage du titre + source
- [ ] Implémenter l'export CSV avec `pandas` (encodage UTF-8 avec BOM pour compatibilité Excel)
- [ ] Implémenter optionnellement l'export JSON et SQLite
- [ ] Valider les données exportées via des règles métier (date future, montant positif, etc.)

---

### Phase 5 — Orchestration et automatisation *(~1 semaine)*

- [ ] Créer un script principal `run_all.py` qui orchestre tous les scrapers en parallèle
- [ ] Mettre en place une planification automatique :
  - Option A : `cron` (Linux/macOS) — exécution quotidienne ou hebdomadaire
  - Option B : GitHub Actions — workflow déclenché sur schedule
- [ ] Implémenter un système de logs structurés (`logging` + rotation des fichiers)
- [ ] Envoyer une notification par email ou Slack en cas d'erreur critique ou de nouvelles entrées
- [ ] Versionner les CSV produits avec un horodatage dans le nom de fichier

```yaml
# .github/workflows/scrape.yml — exemple GitHub Actions
on:
  schedule:
    - cron: '0 6 * * 1'  # Tous les lundis à 6h
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: python run_all.py
      - uses: actions/upload-artifact@v3
        with:
          name: appels_offres
          path: output/
```

---

### Phase 6 — Qualité, maintenance et évolutions *(continu)*

- [ ] Mettre en place des alertes de rupture de scraper (changement de structure HTML)
- [ ] Ajouter un module de scoring de pertinence par mots-clés (NLP léger)
- [ ] Étendre à de nouvelles sources (Europe : Horizon Europe, ERC, etc.)
- [ ] Créer une interface web légère de consultation (optionnel — Flask ou Streamlit)
- [ ] Documenter chaque scraper dans `/docs/`

---

## 🗃️ Structure du projet

```
HealthFundingScraper/
│
├── scrapers/                   # Un fichier par source
│   ├── base_scraper.py
│   ├── bpi_france.py
│   ├── anr.py
│   ├── inca.py
│   ├── anrs.py
│   ├── inserm.py
│   ├── frm.py
│   ├── ans.py
│   ├── ligue_cancer.py
│   ├── fondation_arc.py
│   ├── ars/
│   │   ├── ars_idf.py
│   │   ├── ars_paca.py
│   │   └── ...                 # Un fichier par ARS
│   └── ...
│
├── models/
│   └── appel_offre.py          # Dataclass / Pydantic model
│
├── utils/
│   ├── normalizer.py           # Normalisation montants, dates
│   ├── deduplicator.py
│   └── exporter.py             # CSV, JSON, SQLite
│
├── tests/
│   ├── test_bpi.py
│   ├── test_anr.py
│   └── ...
│
├── output/                     # Fichiers CSV générés (gitignored)
│   └── appels_offres_sante_YYYYMMDD.csv
│
├── docs/
│   ├── source_mapping.md       # Cartographie des sources
│   └── schema.md               # Description du schéma CSV
│
├── .github/
│   └── workflows/
│       └── scrape.yml
│
├── run_all.py                  # Point d'entrée principal
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

```bash
# Cloner le dépôt
git clone https://github.com/votre-user/HealthFundingScraper.git
cd HealthFundingScraper

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer les variables d'environnement
cp .env.example .env
```

---

## ▶️ Utilisation

```bash
# Lancer tous les scrapers
python run_all.py

# Lancer un scraper spécifique
python run_all.py --source bpi_france

# Définir le chemin de sortie
python run_all.py --output ./output/my_export.csv

# Mode dry-run (sans écriture)
python run_all.py --dry-run
```

---

## 📦 Dépendances principales

| Package | Usage |
|---------|-------|
| `requests` | Requêtes HTTP statiques |
| `beautifulsoup4` + `lxml` | Parsing HTML |
| `playwright` | Pages JavaScript dynamiques |
| `pandas` | Manipulation et export CSV |
| `pydantic` | Validation du schéma de données |
| `pdfplumber` | Extraction depuis des PDFs |
| `schedule` | Planification locale |
| `python-dotenv` | Gestion des variables d'environnement |

---

## ⚠️ Considérations légales et éthiques

- Respecter les fichiers `robots.txt` de chaque site
- Introduire des délais entre les requêtes (`time.sleep` aléatoire)
- Ne pas surcharger les serveurs (taux de requêtes raisonnable)
- Les données collectées sont publiques mais leur réutilisation doit respecter les CGU des sites sources
- Aucune donnée personnelle n'est collectée

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour ajouter une nouvelle source :

1. Créer un fichier dans `/scrapers/` héritant de `BaseScraper`
2. Implémenter les méthodes `fetch()`, `parse()` et `normalize()`
3. Ajouter les tests correspondants dans `/tests/`
4. Documenter la source dans `/docs/source_mapping.md`
5. Ouvrir une Pull Request

---

## 📄 Licence

MIT License — voir [LICENSE](LICENSE)

---

> *Projet en développement actif — contributions et retours bienvenus*
