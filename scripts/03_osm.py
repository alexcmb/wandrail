"""
Script 03 - Donnees OpenStreetMap via API Overpass (Pays de la Loire)
----------------------------------------------------------------------
Recupere depuis OSM les types de lieux sous-representes dans DATAtourisme :
  - Restaurants, cafes, bars
  - Parcs et espaces verts
  - Pistes cyclables et voies vertes
  - Stations de velo en libre-service (Velos de la Loire, Tan, etc.)
  - Parkings velo en gare
  - Arrets de bus et de tram

L'API Overpass est gratuite et sans authentification.
On limite les requetes a la bounding box PDL pour eviter les surcharges.

Resultat attendu :
  - silver.mobilites    : stations velo, arrets bus, tram (~500-1000 lignes)
  - silver.cyclables    : voies cyclables (~200-500 lignes)
  - silver.poi          : restaurants et parcs ajoutes (source=osm)
"""

import sys
import os
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


engine = get_engine()

# Bounding box Pays de la Loire : sud, ouest, nord, est
BBOX_PDL = "46.3,-2.6,48.4,1.0"

# URL de l'API Overpass (instance publique)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Pause entre les requetes (respecter les limites de l'API publique)
PAUSE_SECONDES = 3


def requete_overpass(query: str, description: str) -> list:
    """
    Envoie une requete Overpass QL et retourne la liste des elements.
    En cas d'erreur, retourne une liste vide plutot que d'interrompre le script.
    """
    print(f"  Requete OSM : {description}...")
    try:
        r = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=120,
            headers={"User-Agent": "Wandrail-Project/1.0 (M1 BDIA Sup de Vinci)"}
        )
        r.raise_for_status()
        elements = r.json().get("elements", [])
        print(f"    -> {len(elements)} elements recuperes")
        time.sleep(PAUSE_SECONDES)
        return elements
    except Exception as e:
        print(f"    -> Erreur : {e}")
        time.sleep(PAUSE_SECONDES)
        return []


print("=" * 60)
print("SCRIPT 03 - OpenStreetMap Pays de la Loire")
print("=" * 60)


# ============================================================
# PARTIE 1 : Restauration (restaurants, cafes, bars)
# ============================================================
print("\n--- Restauration depuis OSM ---")

query_restauration = f"""
[out:json][timeout:60];
(
  node["amenity"="restaurant"]({BBOX_PDL});
  node["amenity"="cafe"]({BBOX_PDL});
  node["amenity"="bar"]({BBOX_PDL});
  node["amenity"="fast_food"]({BBOX_PDL});
  node["amenity"="pub"]({BBOX_PDL});
);
out body;
"""

elements_resto = requete_overpass(query_restauration, "restaurants, cafes, bars")

pois_osm_resto = []
for el in elements_resto:
    if el.get("type") != "node":
        continue
    tags    = el.get("tags", {})
    nom     = tags.get("name", "")
    lat     = el.get("lat")
    lon     = el.get("lon")
    amenity = tags.get("amenity", "restaurant")

    if not nom or not lat or not lon:
        continue

    # Sous-categorie selon le type OSM
    sous_cat_map = {
        "restaurant": "Restaurant",
        "cafe"      : "Cafe",
        "bar"       : "Bar",
        "fast_food" : "Restauration rapide",
        "pub"       : "Pub",
    }

    pois_osm_resto.append({
        "nom"           : nom[:500],
        "categorie"     : "Restauration",
        "sous_categorie": sous_cat_map.get(amenity, "Restaurant"),
        "commune"       : tags.get("addr:city", "").lower()[:100],
        "code_postal"   : tags.get("addr:postcode", "")[:10],
        "departement"   : None,
        "latitude"      : float(lat),
        "longitude"     : float(lon),
        "telephone"     : tags.get("phone", tags.get("contact:phone", ""))[:50] or None,
        "site_web"      : tags.get("website", tags.get("contact:website", ""))[:500] or None,
        "note_moyenne"  : float(tags.get("stars", 0) or 0),
        "region"        : "Pays de la Loire",
        "source"        : "osm",
        "date_maj"      : None,
    })

print(f"  {len(pois_osm_resto)} restaurants/cafes/bars extraits")


# ============================================================
# PARTIE 2 : Parcs et nature
# ============================================================
print("\n--- Parcs et espaces naturels depuis OSM ---")

query_parcs = f"""
[out:json][timeout:60];
(
  node["leisure"="park"]({BBOX_PDL});
  node["leisure"="nature_reserve"]({BBOX_PDL});
  node["leisure"="garden"]({BBOX_PDL});
  node["natural"="beach"]({BBOX_PDL});
  node["natural"="wood"]({BBOX_PDL});
);
out body;
"""

elements_parcs = requete_overpass(query_parcs, "parcs, reserves naturelles, plages")

pois_osm_nature = []
for el in elements_parcs:
    if el.get("type") != "node":
        continue
    tags = el.get("tags", {})
    nom  = tags.get("name", "")
    lat  = el.get("lat")
    lon  = el.get("lon")

    if not nom or not lat or not lon:
        continue

    leisure = tags.get("leisure", "")
    natural = tags.get("natural", "")

    if natural == "beach":
        sous_cat = "Plage"
    elif natural == "wood":
        sous_cat = "Foret"
    elif leisure == "garden":
        sous_cat = "Jardin"
    elif leisure == "nature_reserve":
        sous_cat = "Reserve naturelle"
    else:
        sous_cat = "Parc"

    pois_osm_nature.append({
        "nom"           : nom[:500],
        "categorie"     : "Nature",
        "sous_categorie": sous_cat,
        "commune"       : tags.get("addr:city", "").lower()[:100],
        "code_postal"   : tags.get("addr:postcode", "")[:10],
        "departement"   : None,
        "latitude"      : float(lat),
        "longitude"     : float(lon),
        "telephone"     : None,
        "site_web"      : tags.get("website", "")[:500] or None,
        "note_moyenne"  : 5.0,  # Les espaces naturels ont un score de base positif
        "region"        : "Pays de la Loire",
        "source"        : "osm",
        "date_maj"      : None,
    })

print(f"  {len(pois_osm_nature)} espaces naturels extraits")


# ============================================================
# PARTIE 3 : Mobilites locales (velos, bus, tram)
# ============================================================
print("\n--- Mobilites locales depuis OSM ---")

query_mobilites = f"""
[out:json][timeout:60];
(
  node["amenity"="bicycle_rental"]({BBOX_PDL});
  node["amenity"="bicycle_parking"]({BBOX_PDL});
  node["highway"="bus_stop"]({BBOX_PDL});
  node["railway"="tram_stop"]({BBOX_PDL});
  node["amenity"="ferry_terminal"]({BBOX_PDL});
);
out body;
"""

elements_mob = requete_overpass(query_mobilites, "velos en libre-service, arrets bus/tram")

mobilites_rows = []
for el in elements_mob:
    if el.get("type") != "node":
        continue
    tags = el.get("tags", {})
    lat  = el.get("lat")
    lon  = el.get("lon")

    if not lat or not lon:
        continue

    amenity  = tags.get("amenity", "")
    highway  = tags.get("highway", "")
    railway  = tags.get("railway", "")
    nom_stat = tags.get("name", tags.get("ref", "Station sans nom"))

    if amenity == "bicycle_rental":
        type_mob   = "velo"
        nb_places  = int(tags.get("capacity", 0) or 0)
    elif amenity == "bicycle_parking":
        type_mob   = "parking_velo"
        nb_places  = int(tags.get("capacity", 0) or 0)
    elif highway == "bus_stop":
        type_mob   = "bus"
        nb_places  = 0
    elif railway == "tram_stop":
        type_mob   = "tram"
        nb_places  = 0
    elif amenity == "ferry_terminal":
        type_mob   = "ferry"
        nb_places  = 0
    else:
        continue

    mobilites_rows.append({
        "type_mobilite"  : type_mob,
        "nom_station"    : str(nom_stat)[:200],
        "commune"        : tags.get("addr:city", tags.get("operator", ""))[:100].lower(),
        "latitude"       : float(lat),
        "longitude"      : float(lon),
        "nb_places"      : nb_places,
        "id_gare_proche" : None,  # sera calcule dans le script 04
        "distance_gare_km": None,
        "source"         : "osm",
    })

print(f"  {len(mobilites_rows)} points de mobilite extraits")


# ============================================================
# PARTIE 4 : Pistes cyclables
# ============================================================
print("\n--- Pistes cyclables depuis OSM ---")

query_cyclables = f"""
[out:json][timeout:90];
(
  way["highway"="cycleway"]({BBOX_PDL});
  way["bicycle"="designated"]({BBOX_PDL});
  way["route"="bicycle"]({BBOX_PDL});
);
out body;
"""

elements_velo = requete_overpass(query_cyclables, "pistes cyclables et voies vertes")

# Les ways OSM n'ont pas de coordonnees directes, on recupere juste les metadonnees
cyclables_rows = []
for el in elements_velo:
    if el.get("type") != "way":
        continue
    tags = el.get("tags", {})
    nom  = tags.get("name", tags.get("ref", "Voie cyclable"))

    # Estimation de longueur depuis le nombre de noeuds (approximation)
    nb_noeuds = len(el.get("nodes", []))
    longueur_approx = round(nb_noeuds * 0.05, 2)  # ~50m par noeud en moyenne

    type_voie = tags.get("highway", tags.get("route", "cycleway"))

    cyclables_rows.append({
        "nom"       : str(nom)[:300],
        "type_voie" : type_voie[:100],
        "longueur_km": longueur_approx,
        "commune"   : tags.get("addr:city", "")[:100].lower(),
    })

print(f"  {len(cyclables_rows)} voies cyclables extraites")


# ============================================================
# INSERTION EN BASE
# ============================================================

# -- Ajout des POI OSM dans silver.poi -----------------------------------------
print("\nInsertion des POI OSM dans silver.poi...")
all_pois_osm = pois_osm_resto + pois_osm_nature

if all_pois_osm:
    df_osm = pd.DataFrame(all_pois_osm)
    df_osm = df_osm.drop_duplicates(subset=["nom", "latitude", "longitude"])

    with engine.connect() as conn:
        for _, row in df_osm.iterrows():
            # Verifier que le POI n'existe pas deja (evite les doublons avec DATAtourisme)
            exist = conn.execute(text("""
                SELECT id FROM silver.poi
                WHERE nom = :nom AND ABS(latitude - :lat) < 0.001 AND ABS(longitude - :lon) < 0.001
                LIMIT 1
            """), {"nom": row["nom"], "lat": row["latitude"], "lon": row["longitude"]}).fetchone()

            if exist:
                continue

            conn.execute(text("""
                INSERT INTO silver.poi
                  (nom, categorie, sous_categorie, commune, code_postal, departement,
                   latitude, longitude, telephone, site_web, note_moyenne,
                   region, source, date_maj)
                VALUES (:nom, :cat, :scat, :com, :cp, :dep, :lat, :lon,
                        :tel, :web, :note, :reg, :src, :dmaj)
            """), {
                "nom" : row["nom"],
                "cat" : row["categorie"],
                "scat": row["sous_categorie"],
                "com" : row["commune"],
                "cp"  : row.get("code_postal"),
                "dep" : None,
                "lat" : row["latitude"],
                "lon" : row["longitude"],
                "tel" : row.get("telephone"),
                "web" : row.get("site_web"),
                "note": float(row.get("note_moyenne", 0)),
                "reg" : "Pays de la Loire",
                "src" : "osm",
                "dmaj": None,
            })
        conn.commit()

    nb_poi = pd.read_sql("SELECT COUNT(*) as n FROM silver.poi WHERE source='osm'", engine).iloc[0]["n"]
    print(f"  {nb_poi} POI OSM dans silver.poi")
else:
    print("  Aucun POI OSM a inserer")


# -- Mobilites dans silver.mobilites -------------------------------------------
print("\nInsertion dans silver.mobilites...")
if mobilites_rows:
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE silver.mobilites RESTART IDENTITY"))
        for row in mobilites_rows:
            conn.execute(text("""
                INSERT INTO silver.mobilites
                  (type_mobilite, nom_station, commune, latitude, longitude,
                   nb_places, id_gare_proche, distance_gare_km, source)
                VALUES (:type, :nom, :com, :lat, :lon, :nb, :gare, :dist, :src)
            """), {
                "type": row["type_mobilite"],
                "nom" : row["nom_station"],
                "com" : row["commune"],
                "lat" : row["latitude"],
                "lon" : row["longitude"],
                "nb"  : row["nb_places"],
                "gare": None,
                "dist": None,
                "src" : "osm",
            })
        conn.commit()
    print(f"  {len(mobilites_rows)} mobilites dans silver.mobilites")
else:
    print("  Aucune mobilite a inserer")


# -- Cyclables dans silver.cyclables -------------------------------------------
print("\nInsertion dans silver.cyclables...")
if cyclables_rows:
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE silver.cyclables RESTART IDENTITY"))
        for row in cyclables_rows:
            conn.execute(text("""
                INSERT INTO silver.cyclables (nom, type_voie, longueur_km, commune)
                VALUES (:nom, :type, :long, :com)
            """), {
                "nom" : row["nom"],
                "type": row["type_voie"],
                "long": row["longueur_km"],
                "com" : row["commune"],
            })
        conn.commit()
    print(f"  {len(cyclables_rows)} voies cyclables dans silver.cyclables")
else:
    print("  Aucune voie cyclable a inserer")


# -- Rapport final -------------------------------------------------------------
print("\n" + "=" * 60)
print("RESUME SCRIPT 03 - OSM")
print("=" * 60)

stats = pd.read_sql("""
    SELECT source, COUNT(*) as nb FROM silver.poi
    GROUP BY source ORDER BY nb DESC
""", engine)
print("\nPOI par source :")
print(stats.to_string(index=False))

cats = pd.read_sql("""
    SELECT categorie, COUNT(*) as nb FROM silver.poi
    GROUP BY categorie ORDER BY nb DESC
""", engine)
print("\nPOI par categorie (apres ajout OSM) :")
print(cats.to_string(index=False))

print("\nScript 03 termine.")
