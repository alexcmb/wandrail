# Wandrail — Découvre la France en train

Projet d'études M1 Big Data & IA — Sup de Vinci  
Diplôme : **RNCP40167** — Expert en ingénierie de données massives et IA (Niveau 7)  
Partenaire : **Fondation SNCF** / Open Data University — Saison 3  
Version actuelle : **Pays de la Loire** · Roadmap : France entière

---

## Problématique

> Comment faciliter et encourager le tourisme en train en France ?

En France, le secteur du tourisme a émis 97 millions de tonnes de CO₂ en 2022. Un trajet de 500 km en train émet **10 fois moins de CO₂** qu'en voiture. Ce projet construit un système data complet pour aider les voyageurs à découvrir les destinations touristiques accessibles depuis les gares des Pays de la Loire.

---

## Architecture globale

```
Sources open data (SNCF, DATAtourisme, OSM, INSEE)
        │
        ▼
┌─────────────────────────────────────────┐
│         PIPELINE ETL (Apache Airflow)   │
│                                         │
│  BRONZE        SILVER         GOLD      │
│  (brut)  ───► (nettoyé) ───► (agrégé)  │
│                                         │
│     PostgreSQL — port 5434              │
│     DB : tourisme_train                 │
└─────────────────────────────────────────┘
        │                    │
        ▼                    ▼
  Modèles ML            Application
  (KMeans + KNN)        Streamlit
  stockés en .pkl       (2 apps)
        │                    │
        ▼                    ▼
  MLflow tracking     app/main.py     → Voyageurs
                      app/analyst.py  → Analystes
```

---

## Structure du projet

```
tourisme_train/
├── app/
│   ├── main.py          # App voyageurs (port 8501)
│   └── analyst.py       # App data analysts (port 8507)
├── scripts/
│   ├── 00_init_db.py    # Création des schémas Bronze/Silver/Gold
│   ├── 01_gares.py      # Ingestion gares SNCF (SNCF Open Data)
│   ├── 02_datatourisme.py   # POI DATAtourisme PDL
│   ├── 03_mobilites.py  # Mobilités locales (vélos, bus)
│   ├── 04_enrichissement.py # Calcul distances gare↔POI (Silver)
│   ├── 05_gold_layer.py # Construction schéma en étoile (Gold)
│   ├── 06_ml_clustering.py  # KMeans — clustering des POI
│   └── 07_ml_recommandation.py # KNN — recommandations par profil
├── airflow/
│   └── dags/
│       └── tourisme_dag.py  # DAG Airflow (orchestration hebdo)
├── models/
│   ├── kmeans_poi.pkl       # Modèle KMeans entraîné
│   └── knn_recommandation.pkl # Modèle KNN entraîné
├── notebooks/               # Analyses exploratoires + évaluation ML
├── data/
│   └── raw/
│       └── liste-des-gares.csv
├── docs/
│   └── audit_donnees.md     # Rapport qualité des données
├── docker-compose.yml       # PostgreSQL + Airflow + Streamlit
├── Dockerfile               # Image Streamlit
├── requirements.txt
├── .env.example             # Variables d'environnement (template)
└── README.md
```

---

## Base de données — Architecture Médaillon

| Schéma | Rôle | Tables principales |
|--------|------|--------------------|
| **bronze** | Données brutes, jamais modifiées | `gares_raw`, `poi_raw`, `mobilites_raw` |
| **silver** | Données nettoyées et structurées | `gares`, `poi`, `poi_enrichi` |
| **gold** | Schéma en étoile pour analyse | `dim_gare`, `dim_poi`, `dim_profil`, `recommandations`, `poi_clusters` |
| **userapp** | Données applicatives | `users`, `user_favorites` |

---

## Modèles ML

### KMeans — Clustering des POI (`06_ml_clustering.py`)
- **Objectif** : regrouper les 14 979 points d'intérêt en clusters thématiques
- **Features** : latitude, longitude, catégorie (encodée), score popularité
- **Métriques** : Silhouette Score, méthode Elbow → voir `notebooks/evaluation_kmeans.ipynb`

### KNN — Recommandations (`07_ml_recommandation.py`)
- **Objectif** : recommander les 5 meilleures destinations pour chaque profil voyageur
- **5 profils** : Famille, Couple, Solo Aventurier, Senior, Groupe Amis
- **Métriques** : Precision@5, Recall@5 → voir `notebooks/evaluation_knn.ipynb`

---

## Installation

### Prérequis
- Python 3.10+
- Docker Desktop (pour PostgreSQL + Airflow)

### Démarrage rapide

```bash
# 1. Cloner le projet
git clone <url-repo>
cd tourisme_train

# 2. Copier les variables d'environnement
cp .env.example .env
# Éditer .env avec tes valeurs

# 3. Installer les dépendances Python
pip install -r requirements.txt

# 4. Lancer PostgreSQL
docker-compose up postgres -d

# 5. Initialiser la base de données
python scripts/00_init_db.py

# 6. Lancer le pipeline ETL complet
python scripts/01_gares.py
python scripts/02_datatourisme.py
python scripts/04_enrichissement.py
python scripts/05_gold_layer.py
python scripts/06_ml_clustering.py
python scripts/07_ml_recommandation.py

# 7. Lancer l'application
streamlit run app/main.py
```

---

## Données utilisées

| Source | Type | Volume (PDL) |
|--------|------|-------------|
| SNCF Open Data | Gares, fréquentation | 254 gares |
| DATAtourisme | Points d'intérêt | 14 979 POI |
| OSM / Overpass | Mobilités locales | En cours |
| INSEE | Population communes | En cours |

---

## Éco-impact

Le calcul CO₂ compare le train aux autres modes de transport sur la base des données ADEME :

| Mode | CO₂ g/km/passager |
|------|-------------------|
| Train TER | 23 |
| Voiture (seul) | 193 |
| Avion | 258 |
| Bus | 103 |

---

## Auteur

**Thilissa Amara** — M1 Big Data & IA, Sup de Vinci  
Promotion 2025-2026
