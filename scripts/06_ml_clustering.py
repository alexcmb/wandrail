"""
Script 06 - KMeans Clustering des POI
--------------------------------------
Etapes :
  1. Charge les POI depuis silver.poi avec les features disponibles
  2. Methode Elbow pour choisir le nombre optimal de clusters (sauvegardee dans docs/)
  3. KMeans avec le nombre optimal de clusters
  4. Calcule le Silhouette Score (metrique de qualite du clustering)
  5. Nomme automatiquement chaque cluster selon la categorie dominante
  6. Sauvegarde le modele dans models/kmeans_poi.pkl
  7. Insere les resultats dans gold.poi_clusters et met a jour gold.dim_poi

Metriques cibles :
  - Silhouette Score > 0.3 (acceptable)
  - Silhouette Score > 0.5 (bon)
"""

import sys
import os
import pickle
import platform
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Mode non-interactif (pas d'interface graphique necessaire)
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score

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

# Noms de clusters associes aux categories DATAtourisme/OSM
CAT_TO_CLUSTER = {
    "Nature"       : ("Nature & Plein air",  "#2ecc71"),
    "Culture"      : ("Culture & Arts",      "#9b59b6"),
    "Patrimoine"   : ("Patrimoine",          "#e67e22"),
    "Restauration" : ("Gastronomie",         "#e74c3c"),
    "Hebergement"  : ("Hebergements",        "#3498db"),
    "Sport & Loisirs": ("Sport & Aventure",  "#f39c12"),
    "Loisirs"      : ("Loisirs & Detente",   "#f39c12"),
    "Evenement"    : ("Evenements",          "#1abc9c"),
    "Commerce"     : ("Commerce & Services", "#95a5a6"),
    "Autre"        : ("Divers",              "#bdc3c7"),
}


print("=" * 60)
print("SCRIPT 06 - KMeans Clustering des POI")
print("=" * 60)


# -- Etape 1 : Chargement ------------------------------------------------------

print("\nChargement des POI depuis silver.poi...")
df = pd.read_sql("""
    SELECT id, nom, categorie, commune, latitude, longitude, note_moyenne
    FROM silver.poi
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
""", engine)
print(f"  {len(df)} POI charges")

if len(df) < 50:
    print("Pas assez de POI pour le clustering. Verifier silver.poi.")
    sys.exit(1)


# -- Etape 2 : Feature Engineering ---------------------------------------------

print("\nPreparation des features...")

# Encode la categorie en valeur numerique
le             = LabelEncoder()
df["cat_enc"]  = le.fit_transform(df["categorie"].fillna("Autre"))

# Normalise la note entre 0 et 1
note_max        = df["note_moyenne"].max()
df["note_norm"] = (df["note_moyenne"].fillna(0) / note_max) if note_max > 0 else 0.0

# Features : position GPS, categorie encodee, note normalisee
X        = df[["latitude", "longitude", "cat_enc", "note_norm"]].copy()
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"  Features utilisees : latitude, longitude, categorie (encodee), note (normalisee)")
print(f"  Matrice X : {X_scaled.shape}")


# -- Etape 3 : Methode Elbow (choix du nombre de clusters) --------------------
# On teste de 2 a 10 clusters et on trace l'inertie (sum of squared distances).
# Le "coude" de la courbe indique le nombre optimal de clusters.

print("\nMethode Elbow (2 a 10 clusters)...")

K_MIN  = 2
K_MAX  = 10
inerties = []
silhouettes = []

# Sous-echantillon pour accelerer si beaucoup de POI
sample_size = min(5000, len(X_scaled))
X_sample    = X_scaled[:sample_size]

for k in range(K_MIN, K_MAX + 1):
    km_tmp = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=200)
    labels_tmp = km_tmp.fit_predict(X_sample)
    inerties.append(km_tmp.inertia_)
    sil = silhouette_score(X_sample, labels_tmp)
    silhouettes.append(sil)
    print(f"  k={k} : inertie={km_tmp.inertia_:.0f}, silhouette={sil:.4f}")

# Sauvegarde du graphe Elbow pour le dossier technique
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

ax1.plot(range(K_MIN, K_MAX + 1), inerties, marker="o", color="#1d4ed8")
ax1.set_title("Methode Elbow - Inertie par k")
ax1.set_xlabel("Nombre de clusters (k)")
ax1.set_ylabel("Inertie")
ax1.grid(True, alpha=0.3)

ax2.plot(range(K_MIN, K_MAX + 1), silhouettes, marker="o", color="#16a34a")
ax2.set_title("Silhouette Score par k")
ax2.set_xlabel("Nombre de clusters (k)")
ax2.set_ylabel("Silhouette Score")
ax2.grid(True, alpha=0.3)

plt.tight_layout()
elbow_path = os.path.join(DOCS_PATH, "elbow_kmeans.png")
plt.savefig(elbow_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"\n  Graphe Elbow sauvegarde : {elbow_path}")

# Choix automatique : k avec le meilleur Silhouette Score
best_k = range(K_MIN, K_MAX + 1)[silhouettes.index(max(silhouettes))]
print(f"\n  Nombre de clusters optimal (max silhouette) : k = {best_k}")


# -- Etape 4 : KMeans avec le k optimal ----------------------------------------

print(f"\nKMeans clustering (k={best_k})...")
kmeans = KMeans(
    n_clusters=best_k,
    random_state=42,
    n_init=20,
    max_iter=300
)
labels = kmeans.fit_predict(X_scaled)
df["cluster_id"] = labels

# Calcul du Silhouette Score sur l'ensemble complet
sil_final = silhouette_score(X_scaled[:sample_size], labels[:sample_size])
print(f"  Silhouette Score final : {sil_final:.4f}")

if sil_final < 0.3:
    print("  Avertissement : Silhouette Score < 0.3. Le clustering est faible.")
    print("  Cause probable : POI trop concentres geographiquement ou categories desequilibrees.")
elif sil_final < 0.5:
    print("  Silhouette Score acceptable (0.3-0.5).")
else:
    print("  Bon Silhouette Score (> 0.5).")


# -- Etape 5 : Nommage des clusters --------------------------------------------

print("\nIdentification des clusters...")
cluster_info = {}

for c_id in range(best_k):
    mask    = df["cluster_id"] == c_id
    cats    = df[mask]["categorie"].value_counts()
    top_cat = cats.index[0] if len(cats) > 0 else "Autre"
    cluster_info[c_id] = {
        "top_categorie": top_cat,
        "nb_poi"       : int(mask.sum()),
    }

# Evite les doublons de noms de clusters
noms_utilises = {}
NOMS_CLUSTERS = {}

for c_id, info in cluster_info.items():
    top_cat     = info["top_categorie"]
    nom, couleur = CAT_TO_CLUSTER.get(top_cat, ("Divers", "#bdc3c7"))

    # Si ce nom est deja utilise, ajouter un suffixe numerique
    compteur = noms_utilises.get(nom, 0) + 1
    noms_utilises[nom] = compteur
    if compteur > 1:
        nom = f"{nom} {compteur}"

    NOMS_CLUSTERS[c_id] = (nom, couleur)
    print(f"  Cluster {c_id} ({info['nb_poi']} POI) -> {nom} [top cat: {top_cat}]")


# -- Etape 6 : Sauvegarde modele -----------------------------------------------

model_data = {
    "kmeans"       : kmeans,
    "scaler"       : scaler,
    "label_encoder": le,
    "noms_clusters": NOMS_CLUSTERS,
    "best_k"       : best_k,
    "silhouette"   : sil_final,
    "feature_names": ["latitude", "longitude", "cat_enc", "note_norm"],
}

model_file = os.path.join(MODEL_PATH, "kmeans_poi.pkl")
with open(model_file, "wb") as f:
    pickle.dump(model_data, f)
print(f"\nModele sauvegarde : {model_file}")


# -- Etape 7 : Insertion dans gold.poi_clusters --------------------------------

print("\nInsertion dans gold.poi_clusters...")

distances_centroides = kmeans.transform(X_scaled)
# Score d'appartenance : inverse de la distance au centroide le plus proche
scores_app = 1.0 / (1.0 + np.min(distances_centroides, axis=1))

df["cluster_nom"]        = df["cluster_id"].map(lambda x: NOMS_CLUSTERS[x][0])
df["cluster_couleur"]    = df["cluster_id"].map(lambda x: NOMS_CLUSTERS[x][1])
df["score_appartenance"] = np.round(scores_app, 4)

# Recuperer les IDs de gold.dim_poi dans le meme ordre
df_dim_poi = pd.read_sql("SELECT id FROM gold.dim_poi ORDER BY id", engine)
df_sorted  = df.sort_values("id").reset_index(drop=True)

with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE gold.poi_clusters RESTART IDENTITY"))
    conn.commit()

clusters_rows = []
for i, row in df_sorted.iterrows():
    if i < len(df_dim_poi):
        clusters_rows.append({
            "id_poi"            : int(df_dim_poi.iloc[i]["id"]),
            "cluster_id"        : int(row["cluster_id"]),
            "cluster_nom"       : row["cluster_nom"],
            "cluster_couleur"   : row["cluster_couleur"],
            "score_appartenance": float(row["score_appartenance"]),
        })

pd.DataFrame(clusters_rows).to_sql(
    "poi_clusters", engine, schema="gold", if_exists="append", index=False
)

# Mettre a jour gold.dim_poi
with engine.connect() as conn:
    for i, row in df_sorted.iterrows():
        if i < len(df_dim_poi):
            conn.execute(text("""
                UPDATE gold.dim_poi
                SET cluster_nom = :nom, score_popularite = :score
                WHERE id = :id
            """), {
                "nom"  : row["cluster_nom"],
                "score": float(row["score_appartenance"]),
                "id"   : int(df_dim_poi.iloc[i]["id"]),
            })
    conn.commit()


# -- Rapport final --------------------------------------------------------------

print("\n" + "=" * 60)
print("RESUME CLUSTERING")
print("=" * 60)
print(f"  Silhouette Score   : {sil_final:.4f}")
print(f"  Nombre de clusters : {best_k}")
print(f"  POI clusterises    : {len(df)}")
print(f"  Graphe Elbow       : {elbow_path}")
print("\n  Repartition :")
for c_id, (nom, couleur) in NOMS_CLUSTERS.items():
    nb  = (df["cluster_id"] == c_id).sum()
    pct = nb / len(df) * 100
    print(f"  {nom:<30} : {nb:>5} POI ({pct:.1f}%)")

print("\nScript 06 termine.")
