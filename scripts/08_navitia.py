"""
Script 08 - Isochrones SNCF via API Navitia
--------------------------------------------
L'API Navitia (api.navitia.io) permet de calculer des isochrones :
la zone geographique accessible depuis une gare en un temps donne en train.

Ce script :
  1. Calcule les isochrones depuis les gares principales PDL (Nantes, Le Mans,
     Angers, La Roche-sur-Yon, Laval)
  2. Pour 3 horizons : 1h, 2h, 3h de trajet en train
  3. Stocke les resultats dans gold.isochrones (creee si absente)
  4. Calcule aussi les gares accessibles depuis chaque gare PDL en moins de 3h

Inscription gratuite sur https://navitia.io/register
La cle d'API est a ajouter dans .env : NAVITIA_API_KEY=xxx

Sans cle Navitia, le script calcule des isochrones approximatifs base sur
la vitesse moyenne des trains (130 km/h) et la distance Haversine.
"""

import sys
import os
import math
import json
import time
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()


# -- Connexion ---------------------------------------------------------------

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '00000')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5434')}"
        f"/{os.getenv('DB_NAME', 'tourisme_train')}"
    )


engine       = get_engine()
NAVITIA_KEY  = os.getenv("NAVITIA_API_KEY", "")
NAVITIA_URL  = "https://api.navitia.io/v1"

# Gares principales PDL depuis lesquelles on calcule les isochrones
# Ces gares sont les points de depart les plus frequentes en PDL
GARES_PRINCIPALES = {
    "Nantes"           : {"lat": 47.2178, "lon": -1.5420, "uic": "87481002"},
    "Le Mans"          : {"lat": 48.0028, "lon": 0.1928,  "uic": "87396002"},
    "Angers"           : {"lat": 47.4637, "lon": -0.5507, "uic": "87484006"},
    "La Roche-sur-Yon" : {"lat": 46.6702, "lon": -1.4261, "uic": "87481200"},
    "Laval"            : {"lat": 48.0667, "lon": -0.7700, "uic": "87478008"},
    "Saint-Nazaire"    : {"lat": 47.2742, "lon": -2.2087, "uic": "87481598"},
}

# Durees d'isochrone en secondes
DUREES_ISOCHRONE = {
    "1h"  : 3600,
    "2h"  : 7200,
    "3h"  : 10800,
}

# Vitesse moyenne approximative des trains regionaux (pour le mode sans API)
VITESSE_TRAIN_KMPH = 130


def haversine_km(lat1, lon1, lat2, lon2):
    """Distance en km entre deux points GPS (formule Haversine)."""
    R = 6371
    la1, lo1, la2, lo2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return R * 2 * math.asin(math.sqrt(a))


print("=" * 60)
print("SCRIPT 08 - Isochrones Navitia (SNCF)")
print("=" * 60)


# -- Creation de la table isochrones si elle n'existe pas ----------------------

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS gold.isochrones (
            id               SERIAL PRIMARY KEY,
            nom_gare_depart  VARCHAR(100),
            lat_depart       FLOAT,
            lon_depart       FLOAT,
            duree_label      VARCHAR(10),
            duree_secondes   INTEGER,
            nb_gares_access  INTEGER DEFAULT 0,
            gares_accessibles TEXT,
            methode          VARCHAR(20) DEFAULT 'approximation',
            date_calcul      TIMESTAMP DEFAULT NOW()
        )
    """))
    conn.execute(text("TRUNCATE TABLE gold.isochrones RESTART IDENTITY"))
    conn.commit()

print("\nTable gold.isochrones prete.")


# -- Chargement de toutes les gares PDL pour le calcul -------------------------

df_gares = pd.read_sql(
    "SELECT id, nom_gare, commune, latitude, longitude FROM silver.gares WHERE latitude IS NOT NULL",
    engine
)
print(f"\n{len(df_gares)} gares PDL chargees pour le calcul.")


# -- Mode 1 : API Navitia (si cle disponible) ----------------------------------

def calculer_isochrone_navitia(nom_gare, lat, lon, duree_s):
    """
    Appelle l'API Navitia pour obtenir la liste des arrets accessibles
    depuis un point GPS en un temps donne.
    Retourne la liste des noms de gares accessibles.
    """
    endpoint = f"{NAVITIA_URL}/coverage/fr-sw/journeys"
    params = {
        "from"     : f"{lon};{lat}",
        "max_duration": duree_s,
        "forbidden_uris[]": [],
        "count"    : 50,
    }
    headers = {"Authorization": NAVITIA_KEY}

    try:
        r = requests.get(endpoint, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data     = r.json()
        journeys = data.get("journeys", [])

        destinations = set()
        for j in journeys:
            dest = j.get("sections", [{}])[-1].get("to", {})
            name = dest.get("name", "")
            if name:
                destinations.add(name)

        return list(destinations)
    except Exception as e:
        print(f"    Erreur Navitia pour {nom_gare} : {e}")
        return []


# -- Mode 2 : Approximation geometrique (sans API) -----------------------------

def calculer_isochrone_approximatif(lat_dep, lon_dep, duree_s, df_gares_pdl):
    """
    Calcule les gares accessibles en moins de duree_s secondes
    en supposant une vitesse moyenne de VITESSE_TRAIN_KMPH.

    C'est une approximation : on ne tient pas compte des horaires reels
    ni des connexions. Utile quand l'API Navitia n'est pas disponible.
    """
    rayon_km    = (duree_s / 3600) * VITESSE_TRAIN_KMPH
    accessibles = []

    for _, gare in df_gares_pdl.iterrows():
        dist = haversine_km(lat_dep, lon_dep, gare["latitude"], gare["longitude"])
        if dist <= rayon_km:
            accessibles.append(str(gare["nom_gare"]).title())

    return accessibles


# -- Calcul des isochrones pour chaque gare principale ------------------------

print(f"\nMode : {'Navitia API' if NAVITIA_KEY else 'Approximation geometrique (pas de cle Navitia)'}")
if not NAVITIA_KEY:
    print("  Pour activer le mode Navitia : ajouter NAVITIA_API_KEY=votre_cle dans .env")
    print("  Inscription gratuite : https://navitia.io/register")

print()
rows_isochrones = []

for nom_gare, infos in GARES_PRINCIPALES.items():
    lat = infos["lat"]
    lon = infos["lon"]
    print(f"  Calcul pour {nom_gare} ({lat}, {lon})")

    for label, duree_s in DUREES_ISOCHRONE.items():
        if NAVITIA_KEY:
            gares_acc = calculer_isochrone_navitia(nom_gare, lat, lon, duree_s)
            methode   = "navitia"
            time.sleep(1)  # respect des limites de l'API
        else:
            gares_acc = calculer_isochrone_approximatif(lat, lon, duree_s, df_gares)
            methode   = "approximation"

        print(f"    {label} : {len(gares_acc)} gares accessibles")

        rows_isochrones.append({
            "nom_gare_depart" : nom_gare,
            "lat_depart"      : lat,
            "lon_depart"      : lon,
            "duree_label"     : label,
            "duree_secondes"  : duree_s,
            "nb_gares_access" : len(gares_acc),
            "gares_accessibles": json.dumps(gares_acc, ensure_ascii=False),
            "methode"         : methode,
        })


# -- Insertion en base ---------------------------------------------------------

print("\nInsertion dans gold.isochrones...")
with engine.connect() as conn:
    for row in rows_isochrones:
        conn.execute(text("""
            INSERT INTO gold.isochrones
              (nom_gare_depart, lat_depart, lon_depart, duree_label,
               duree_secondes, nb_gares_access, gares_accessibles, methode)
            VALUES (:dep, :lat, :lon, :label, :sec, :nb, :gares, :meth)
        """), {
            "dep"  : row["nom_gare_depart"],
            "lat"  : row["lat_depart"],
            "lon"  : row["lon_depart"],
            "label": row["duree_label"],
            "sec"  : row["duree_secondes"],
            "nb"   : row["nb_gares_access"],
            "gares": row["gares_accessibles"],
            "meth" : row["methode"],
        })
    conn.commit()

print(f"  {len(rows_isochrones)} isochrones inseres")


# -- Rapport -------------------------------------------------------------------

print("\n" + "=" * 60)
print("RESUME ISOCHRONES")
print("=" * 60)

df_iso = pd.read_sql("""
    SELECT nom_gare_depart, duree_label, nb_gares_access, methode
    FROM gold.isochrones
    ORDER BY nom_gare_depart, duree_label
""", engine)
print(df_iso.to_string(index=False))

print("\nScript 08 termine.")
print("Pour activer le mode Navitia : NAVITIA_API_KEY=xxx dans .env")
