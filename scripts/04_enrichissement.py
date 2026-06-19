"""
Script 04 - Enrichissement POI et Gares
----------------------------------------
1. Calcule la distance Haversine entre chaque POI et toutes les gares PDL
2. Calcule le temps de marche estime (vitesse pietonne 5 km/h)
3. Identifie le top 3 gares les plus proches de chaque POI
4. Insere dans silver.poi_enrichi

Resultat attendu : autant de lignes que silver.poi (26 000+)
"""

import sys, os, math
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER','postgres')}:{os.getenv('DB_PASSWORD','00000')}"
        f"@{os.getenv('DB_HOST','localhost')}:{os.getenv('DB_PORT','5434')}/{os.getenv('DB_NAME','tourisme_train')}"
    )

engine = get_engine()

print("=" * 60)
print("SCRIPT 04 - Enrichissement POI / Gares")
print("=" * 60)


# -- Etape 1 : Chargement ------------------------------------------------------

print("\nChargement des donnees Silver...")
df_gares = pd.read_sql("SELECT id, nom_gare, commune, latitude, longitude FROM silver.gares", engine)
df_poi   = pd.read_sql("SELECT id, nom, categorie, commune, latitude, longitude FROM silver.poi", engine)
print(f"  {len(df_gares)} gares / {len(df_poi)} POI")

if len(df_gares) == 0:
    print("Aucune gare dans silver.gares - executez d'abord le script 01")
    sys.exit(1)


# -- Etape 2 : Fonction distance Haversine ------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Distance en km entre deux points GPS (formule Haversine)."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


# -- Etape 3 : Calcul distances -----------------------------------------------

print("\nCalcul distances POI / Gares...")
print(f"  Traitement de {len(df_poi)} POI x {len(df_gares)} gares...")

gares_arr = df_gares[['id','nom_gare','latitude','longitude']].values
resultats = []

for i, poi in df_poi.iterrows():
    distances = []
    for gare in gares_arr:
        id_g, nom_g, lat_g, lon_g = gare
        try:
            d = haversine(poi['latitude'], poi['longitude'], float(lat_g), float(lon_g))
            distances.append((id_g, nom_g, d))
        except Exception:
            continue

    if not distances:
        continue

    distances.sort(key=lambda x: x[2])
    top3 = distances[:3]

    gare1 = top3[0] if len(top3) > 0 else (None, None, None)
    gare2 = top3[1] if len(top3) > 1 else (None, None, None)
    gare3 = top3[2] if len(top3) > 2 else (None, None, None)

    dist_km      = round(gare1[2], 3)
    temps_marche = round((dist_km / 5.0) * 60, 1)

    resultats.append({
        "id_poi"          : int(poi['id']),
        "id_gare_1"       : int(gare1[0]) if gare1[0] is not None else None,
        "id_gare_2"       : int(gare2[0]) if gare2[0] is not None else None,
        "id_gare_3"       : int(gare3[0]) if gare3[0] is not None else None,
        "nom_gare"        : str(gare1[1]) if gare1[1] else None,
        "distance_gare_km": dist_km,
        "temps_marche_min": temps_marche,
        "categorie"       : poi['categorie'],
        "region"          : "Pays de la Loire",
    })

    if (i + 1) % 1000 == 0:
        print(f"   -> {i + 1}/{len(df_poi)} POI traites...")

df_enrichi = pd.DataFrame(resultats)
print(f"\n  {len(df_enrichi)} POI enrichis.")


# -- Statistiques --------------------------------------------------------------

print(f"\nStatistiques enrichissement :")
print(f"  Distance moyenne gare : {df_enrichi['distance_gare_km'].mean():.2f} km")
print(f"  POI a moins de 2 km   : {(df_enrichi['distance_gare_km'] <= 2).sum()}")
print(f"  POI a moins de 5 km   : {(df_enrichi['distance_gare_km'] <= 5).sum()}")
print(f"  POI a moins de 10 km  : {(df_enrichi['distance_gare_km'] <= 10).sum()}")
print(f"  Temps marche moyen    : {df_enrichi['temps_marche_min'].mean():.1f} min")


# -- Etape 4 : Insertion Silver -----------------------------------------------

print("\nInsertion dans silver.poi_enrichi...")
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE silver.poi_enrichi RESTART IDENTITY"))
    records_e = []
    for _, row in df_enrichi.iterrows():
        records_e.append({
            "poi" : int(row['id_poi']),
            "g1"  : int(row['id_gare_1']) if pd.notna(row['id_gare_1']) else None,
            "g2"  : int(row['id_gare_2']) if pd.notna(row['id_gare_2']) else None,
            "g3"  : int(row['id_gare_3']) if pd.notna(row['id_gare_3']) else None,
            "nom" : row['nom_gare'] if pd.notna(row['nom_gare']) else None,
            "dist": float(row['distance_gare_km']),
            "tps" : float(row['temps_marche_min']),
            "cat" : row['categorie'],
            "reg" : row['region'],
        })
    
    # Bulk insert
    batch_size = 1000
    for i in range(0, len(records_e), batch_size):
        batch = records_e[i:i+batch_size]
        conn.execute(text("""
            INSERT INTO silver.poi_enrichi
              (id_poi, id_gare_1, id_gare_2, id_gare_3, nom_gare,
               distance_gare_km, temps_marche_min, categorie, region)
            VALUES (:poi, :g1, :g2, :g3, :nom, :dist, :tps, :cat, :reg)
        """), batch)
    conn.commit()

nb = pd.read_sql("SELECT COUNT(*) as n FROM silver.poi_enrichi", engine).iloc[0]['n']
print(f"  {nb} lignes dans silver.poi_enrichi")


# -- Compatibilite table public.poi_enrichi -----------------------------------

print("\nMise a jour de public.poi_enrichi (compatibilite app)...")
try:
    df_compat = pd.read_sql("""
        SELECT pe.id as id_poi,
               p.nom as nom_poi,
               pe.categorie,
               p.commune,
               p.latitude,
               p.longitude,
               'Pays de la Loire' as region,
               p.source as source,
               g.id as id_gare_proche,
               pe.nom_gare as nom_gare_proche,
               pe.distance_gare_km
        FROM silver.poi_enrichi pe
        JOIN silver.poi p ON p.id = pe.id_poi
        LEFT JOIN silver.gares g ON g.id = pe.id_gare_1
    """, engine)
    df_compat.to_sql('poi_enrichi', engine, if_exists='replace', index=False)
    print(f"  {len(df_compat)} lignes dans public.poi_enrichi")
except Exception as e:
    print(f"  Erreur compatibilite : {e}")


print("\nScript 04 termine.")
