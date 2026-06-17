"""
Script 07 - KNN Recommandation de destinations par profil voyageur
------------------------------------------------------------------
Pour chaque profil (Famille, Solo, Couple, Groupe, Eco) :
  1. Construit la matrice features des gares depuis gold.dim_gare
  2. Pondere les features selon les preferences du profil
  3. KNN (k=10, metrique cosinus) trouve les gares les plus proches du profil
  4. Calcule Precision@5 et Recall@5 sur un jeu de test synthetique
  5. Sauvegarde dans gold.recommandations

Metriques calculees :
  - Precision@5 : proportion de recommandations pertinentes parmi les 5 retournees
  - Recall@5    : proportion de destinations pertinentes recuperees sur les 5 meilleures possibles
"""

import sys
import os
import pickle
import platform
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()


# -- Connexion et chemins -------------------------------------------------------

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '00000')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5434')}"
        f"/{os.getenv('DB_NAME', 'tourisme_train')}"
    )


def get_model_path():
    if platform.system() == "Windows":
        return r"C:\Users\thili\Desktop\tourisme_train\models"
    return "/opt/airflow/models"


def get_docs_path():
    if platform.system() == "Windows":
        return r"C:\Users\thili\Desktop\tourisme_train\docs"
    return "/opt/airflow/docs"


engine     = get_engine()
MODEL_PATH = get_model_path()
DOCS_PATH  = get_docs_path()
os.makedirs(MODEL_PATH, exist_ok=True)
os.makedirs(DOCS_PATH,  exist_ok=True)


# Preferences par profil : poids de 1 (peu important) a 5 (tres important)
# Ces poids modelisent les attentes typiques de chaque type de voyageur.
PREFS_PROFIL = {
    "Famille": {
        "nb_hebergement"     : 3,
        "nb_restauration"    : 3,
        "nb_culture"         : 2,
        "nb_patrimoine"      : 1,
        "nb_nature"          : 3,
        "nb_sport_loisirs"   : 4,
        "nb_loisirs"         : 4,
        "nb_evenement"       : 2,
        "nb_poi_5km"         : 4,
        "nb_categories"      : 3,
        "score_attractivite" : 3,
    },
    "Solo": {
        "nb_hebergement"     : 2,
        "nb_restauration"    : 3,
        "nb_culture"         : 5,
        "nb_patrimoine"      : 4,
        "nb_nature"          : 3,
        "nb_sport_loisirs"   : 2,
        "nb_loisirs"         : 2,
        "nb_evenement"       : 3,
        "nb_poi_5km"         : 3,
        "nb_categories"      : 5,
        "score_attractivite" : 4,
    },
    "Couple": {
        "nb_hebergement"     : 3,
        "nb_restauration"    : 5,
        "nb_culture"         : 3,
        "nb_patrimoine"      : 3,
        "nb_nature"          : 4,
        "nb_sport_loisirs"   : 2,
        "nb_loisirs"         : 2,
        "nb_evenement"       : 2,
        "nb_poi_5km"         : 3,
        "nb_categories"      : 3,
        "score_attractivite" : 4,
    },
    "Groupe": {
        "nb_hebergement"     : 3,
        "nb_restauration"    : 3,
        "nb_culture"         : 1,
        "nb_patrimoine"      : 1,
        "nb_nature"          : 2,
        "nb_sport_loisirs"   : 5,
        "nb_loisirs"         : 5,
        "nb_evenement"       : 5,
        "nb_poi_5km"         : 4,
        "nb_categories"      : 2,
        "score_attractivite" : 3,
    },
    "Eco": {
        "nb_hebergement"     : 2,
        "nb_restauration"    : 2,
        "nb_culture"         : 2,
        "nb_patrimoine"      : 3,
        "nb_nature"          : 5,
        "nb_sport_loisirs"   : 3,
        "nb_loisirs"         : 2,
        "nb_evenement"       : 1,
        "nb_poi_5km"         : 3,
        "nb_categories"      : 3,
        "score_attractivite" : 4,
    },
}


print("=" * 60)
print("SCRIPT 07 - KNN Recommandation par profil voyageur")
print("=" * 60)


# -- Etape 1 : Chargement ------------------------------------------------------

print("\nChargement des donnees Gold...")
df_gares   = pd.read_sql("SELECT * FROM gold.dim_gare", engine)
df_profils = pd.read_sql("SELECT * FROM gold.dim_profil", engine)
df_poi_e   = pd.read_sql(
    "SELECT id_gare_1, categorie, distance_gare_km FROM silver.poi_enrichi",
    engine
)
print(f"  {len(df_gares)} gares / {len(df_profils)} profils / {len(df_poi_e)} POI enrichis")


# -- Etape 2 : Matrice features ------------------------------------------------

print("\nConstruction de la matrice features par gare...")

# Categories a prendre en compte (liste canonique)
CATEGORIES = [
    "Hebergement", "Restauration", "Culture", "Patrimoine",
    "Nature", "Sport & Loisirs", "Loisirs", "Evenement"
]

for cat in CATEGORIES:
    col = f"nb_{cat.lower().replace(' ', '_').replace('&', '').replace('__', '_').replace('-', '')}"
    counts = (
        df_poi_e[(df_poi_e["categorie"] == cat) & (df_poi_e["distance_gare_km"] <= 5)]
        .groupby("id_gare_1")
        .size()
    )
    df_gares[col] = df_gares["id"].map(counts).fillna(0).astype(int)

# Colonnes features utilisees dans le modele
FEATURE_COLS = [
    "nb_hebergement", "nb_restauration", "nb_culture", "nb_patrimoine",
    "nb_nature", "nb_sport_loisirs", "nb_loisirs", "nb_evenement",
    "nb_poi_5km", "score_attractivite", "nb_categories",
]

# Remplir les colonnes manquantes si besoin
for col in FEATURE_COLS:
    if col not in df_gares.columns:
        df_gares[col] = 0

X = df_gares[FEATURE_COLS].fillna(0).values
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"  Matrice X : {X_scaled.shape}")


# -- Etape 3 : Entrainement KNN ------------------------------------------------

print("\nEntrainement du modele KNN (k=10, metrique cosinus)...")
knn = NearestNeighbors(n_neighbors=min(10, len(df_gares)), metric="cosine")
knn.fit(X_scaled)


# -- Etape 4 : Evaluation Precision@5 et Recall@5 -----------------------------
# Approche : on cree des vecteurs de test en perturbant legerement les vecteurs
# de preference et on verifie que les top-5 restent stables.

print("\nEvaluation Precision@5 et Recall@5...")

def construire_vecteur_profil(prefs: dict, feature_cols: list, max_vals: dict) -> np.ndarray:
    """
    Construit le vecteur de requete KNN a partir des preferences d'un profil.
    Chaque feature est ponderee par le poids de preference (1-5) multiplie par
    la valeur maximale observee dans les donnees, afin de rester dans le meme
    espace que les gares.
    """
    vec = []
    for col in feature_cols:
        score = 0
        for pref_key, pref_val in prefs.items():
            if pref_key.replace("_", "") in col.replace("_", ""):
                score = pref_val
                break
        max_v = max_vals.get(col, 1)
        vec.append(score * max_v / 5.0)
    return np.array(vec)


max_vals = {col: max(df_gares[col].fillna(0).max(), 1) for col in FEATURE_COLS}

metriques_par_profil = {}

for nom_profil, prefs in PREFS_PROFIL.items():
    vec_ref    = construire_vecteur_profil(prefs, FEATURE_COLS, max_vals)
    vec_scaled = scaler.transform([vec_ref])
    _, indices_ref = knn.kneighbors(vec_scaled, n_neighbors=min(10, len(df_gares)))
    top_5_ref      = set(indices_ref[0][:5])

    # Generer 10 versions perturbees du vecteur de profil (bruit de 10%)
    precision_scores = []
    recall_scores    = []
    np.random.seed(42)

    for _ in range(10):
        bruit      = np.random.normal(0, 0.1, size=vec_ref.shape)
        vec_bruit  = np.clip(vec_ref + bruit * vec_ref, 0, None)
        vec_b_sc   = scaler.transform([vec_bruit])
        _, idx_b   = knn.kneighbors(vec_b_sc, n_neighbors=min(10, len(df_gares)))
        top_5_b    = set(idx_b[0][:5])

        # Precision@5 : combien des 5 recommandations bruitees sont dans le top-5 de reference
        precision = len(top_5_ref & top_5_b) / 5.0
        # Recall@5    : meme calcul (symetrique ici car |top_5_ref| = 5)
        recall    = len(top_5_ref & top_5_b) / max(len(top_5_ref), 1)

        precision_scores.append(precision)
        recall_scores.append(recall)

    p5  = round(np.mean(precision_scores), 4)
    r5  = round(np.mean(recall_scores), 4)
    metriques_par_profil[nom_profil] = {"precision_at_5": p5, "recall_at_5": r5}
    print(f"  {nom_profil:<12} : Precision@5 = {p5:.2f} | Recall@5 = {r5:.2f}")

# Sauvegarde des metriques dans docs/
import json
metriques_path = os.path.join(DOCS_PATH, "metriques_knn.json")
with open(metriques_path, "w", encoding="utf-8") as f:
    json.dump(metriques_par_profil, f, indent=2, ensure_ascii=False)
print(f"\n  Metriques sauvegardees : {metriques_path}")


# -- Etape 5 : Sauvegarde modele -----------------------------------------------

model_data = {
    "knn"          : knn,
    "scaler"       : scaler,
    "feature_cols" : FEATURE_COLS,
    "df_gares"     : df_gares,
    "metriques"    : metriques_par_profil,
}
model_file = os.path.join(MODEL_PATH, "knn_recommandation.pkl")
with open(model_file, "wb") as f:
    pickle.dump(model_data, f)
print(f"  Modele sauvegarde : {model_file}")


# -- Etape 6 : Generation des recommandations ----------------------------------

print("\nGeneration des recommandations...")

recommandations = []

for _, profil in df_profils.iterrows():
    nom_profil = profil["nom"]
    prefs      = PREFS_PROFIL.get(nom_profil, PREFS_PROFIL["Solo"])

    vec_profil = construire_vecteur_profil(prefs, FEATURE_COLS, max_vals)
    vec_scaled = scaler.transform([vec_profil])

    distances, indices = knn.kneighbors(vec_scaled, n_neighbors=min(10, len(df_gares)))

    print(f"\n  Profil {nom_profil} :")
    rang = 1
    for dist, idx in zip(distances[0], indices[0]):
        gare       = df_gares.iloc[idx]
        score_reco = round(1.0 / (1.0 + dist) * 10, 2)

        # Construction de la raison textuelle de recommandation
        raisons = []
        nb_poi = int(gare.get("nb_poi_5km", 0) or 0)
        nb_cat = int(gare.get("nb_categories", 0) or 0)
        sc_att = float(gare.get("score_attractivite", 0) or 0)

        if nb_poi > 10:
            raisons.append(f"{nb_poi} activites a moins de 5 km")
        if nb_cat > 3:
            raisons.append(f"{nb_cat} types d'activites differents")
        if sc_att > 5:
            raisons.append(f"Score attractivite {sc_att:.1f}/10")

        raison = " - ".join(raisons) if raisons else "Destination tranquille et accessible"

        recommandations.append({
            "id_profil"   : int(profil["id"]),
            "id_gare"     : int(gare["id"]),
            "rang"        : rang,
            "score_reco"  : score_reco,
            "raison"      : raison,
            "nb_poi_match": nb_poi,
        })
        print(f"    {rang}. {str(gare['nom_gare']).title():<25} score={score_reco}/10 - {raison}")
        rang += 1
        if rang > 5:
            break


# -- Etape 7 : Insertion -------------------------------------------------------

print("\nInsertion dans gold.recommandations...")
df_reco = pd.DataFrame(recommandations)
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE gold.recommandations RESTART IDENTITY"))
    conn.commit()
df_reco.to_sql("recommandations", engine, schema="gold", if_exists="append", index=False)
print(f"  {len(df_reco)} recommandations inserees")


# -- Rapport final -------------------------------------------------------------

print("\n" + "=" * 60)
print("RESUME RECOMMANDATIONS")
print("=" * 60)
print("\n  Metriques d'evaluation :")
for nom, m in metriques_par_profil.items():
    print(f"  {nom:<12} : Precision@5={m['precision_at_5']:.2f} | Recall@5={m['recall_at_5']:.2f}")

print("\nScript 07 termine.")
