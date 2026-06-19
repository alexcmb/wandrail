"""
Script 02 - Points d'interet DATAtourisme (Pays de la Loire)
-------------------------------------------------------------
Etapes :
  1. Appelle l'API DATAtourisme pour recuperer tous les POI PDL
  2. Extrait nom, categorie, commune, GPS, telephone, site web
  3. Calcule un score de popularite synthetique base sur les donnees disponibles
  4. Insere dans bronze.poi_raw puis silver.poi

Score de popularite (0-10) :
  - POI avec site web      : +3 pts
  - POI avec telephone     : +2 pts
  - Categorie rare (< 5%)  : +2 pts  (valorise la diversite)
  - POI recemment mis a jour (< 6 mois) : +3 pts
  - Score normalise entre 0 et 10

Resultat attendu : 10 000 - 15 000 POI en Pays de la Loire
"""

import sys
import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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


engine  = get_engine()
API_KEY = os.getenv("DATATOURISME_API_KEY", "0f58925d-4b95-4ca2-b41b-9d7ea9527421")
URL_DT  = f"https://diffuseur.datatourisme.fr/webservice/b4c0271347c8681f390b852d8937d2e5/{API_KEY}"

# Bounding box Pays de la Loire
LAT_MIN, LAT_MAX = 46.3, 48.4
LON_MIN, LON_MAX = -2.6,  1.0

# Mapping types DATAtourisme -> categories normalisees Wandrail
CATEGORIES = {
    "Accommodation"          : "Hebergement",
    "Hotel"                  : "Hebergement",
    "Camping"                : "Hebergement",
    "Gite"                   : "Hebergement",
    "BedAndBreakfast"        : "Hebergement",
    "Hostel"                 : "Hebergement",
    "Restaurant"             : "Restauration",
    "FoodEstablishment"      : "Restauration",
    "Cafe"                   : "Restauration",
    "FastFoodRestaurant"     : "Restauration",
    "Winery"                 : "Restauration",
    "Museum"                 : "Culture",
    "CulturalSite"           : "Culture",
    "Theater"                : "Culture",
    "Library"                : "Culture",
    "ArtGallery"             : "Culture",
    "Church"                 : "Patrimoine",
    "Castle"                 : "Patrimoine",
    "ReligiousSite"          : "Patrimoine",
    "Monument"               : "Patrimoine",
    "HistoricBuilding"       : "Patrimoine",
    "NaturalHeritage"        : "Nature",
    "Park"                   : "Nature",
    "Beach"                  : "Nature",
    "Lake"                   : "Nature",
    "Forest"                 : "Nature",
    "Garden"                 : "Nature",
    "SportsAndLeisurePlace"  : "Sport & Loisirs",
    "Sport"                  : "Sport & Loisirs",
    "LeisureSportComplexe"   : "Sport & Loisirs",
    "EntertainmentAndEvent"  : "Evenement",
    "Festival"               : "Evenement",
    "ExhibitionEvent"        : "Evenement",
    "Cinema"                 : "Loisirs",
    "TouristInformationCenter": "Service",
    "Store"                  : "Commerce",
    "PointOfInterest"        : "Autre",
}


print("=" * 60)
print("SCRIPT 02 - DATAtourisme Pays de la Loire")
print("=" * 60)


# -- Etape 1 : Appel API -------------------------------------------------------

print("\nConnexion a l'API DATAtourisme...")
try:
    r = requests.get(URL_DT, timeout=120)
    r.raise_for_status()
    data  = r.json()
    graph = data.get("@graph", data) if isinstance(data, dict) else data
    print(f"  {len(graph)} items recus de l'API")
except Exception as e:
    print(f"Erreur API : {e}")
    sys.exit(1)


# -- Etape 2 : Bronze -----------------------------------------------------------

print("\nBronze - insertion donnees brutes...")
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE bronze.poi_raw RESTART IDENTITY"))
    records = []
    for item in graph:
        try:
            ident = item.get("@id", "")
            nom_b = ""
            if "rdfs:label" in item:
                lab = item["rdfs:label"]
                if isinstance(lab, dict):
                    nom_b = lab.get("@value", "") or lab.get("fr", "")
                elif isinstance(lab, list):
                    for l in lab:
                        if isinstance(l, dict) and l.get("@language") == "fr":
                            nom_b = l.get("@value", "")
                            break

            types    = item.get("@type", [])
            if isinstance(types, str):
                types = [types]
            type_raw = "|".join(types[:5])

            records.append({
                "json": json.dumps(item, ensure_ascii=False)[:5000],
                "id"  : ident,
                "nom" : str(nom_b)[:200],
                "type": type_raw[:200],
                "reg" : "Pays de la Loire",
            })
        except Exception:
            continue

    # Bulk insert
    batch_size = 1000
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        conn.execute(text("""
            INSERT INTO bronze.poi_raw (json_brut, identifiant, nom, type_raw, region)
            VALUES (:json, :id, :nom, :type, :reg)
        """), batch)
    conn.commit()
    count_b = len(records)

print(f"  {count_b} lignes dans bronze.poi_raw")


# -- Fonctions d'extraction ----------------------------------------------------

def extraire_nom(item):
    """Extrait le nom en francais depuis rdfs:label."""
    if "rdfs:label" in item:
        lab = item["rdfs:label"]
        if isinstance(lab, dict):
            v = lab.get("@value", "") or lab.get("fr", "")
            return str(v).strip() if not isinstance(v, list) else (str(v[0]).strip() if v else "")
        elif isinstance(lab, list):
            for l in lab:
                if isinstance(l, dict) and l.get("@language") == "fr":
                    return str(l.get("@value", "")).strip()
    return ""


def extraire_coordonnees(item):
    """Extrait latitude et longitude depuis isLocatedAt ou schema:geo."""
    lat, lon = None, None
    loc = item.get("isLocatedAt") or item.get("schema:geo")
    if not loc:
        return lat, lon
    if isinstance(loc, list):
        loc = loc[0]
    geo = loc.get("schema:geo") if isinstance(loc, dict) else loc
    if not geo:
        return lat, lon
    if isinstance(geo, list):
        geo = geo[0]
    try:
        lat_r = geo.get("schema:latitude", {})
        lon_r = geo.get("schema:longitude", {})
        lat = float(lat_r.get("@value", 0) if isinstance(lat_r, dict) else lat_r or 0)
        lon = float(lon_r.get("@value", 0) if isinstance(lon_r, dict) else lon_r or 0)
    except (ValueError, TypeError):
        pass
    return lat, lon


def extraire_commune(item):
    """Extrait la commune depuis schema:address."""
    loc = item.get("isLocatedAt", {})
    if isinstance(loc, list):
        loc = loc[0]
    addr = loc.get("schema:address", {}) if isinstance(loc, dict) else {}
    if isinstance(addr, list):
        addr = addr[0]
    if isinstance(addr, dict):
        return str(addr.get("schema:addressLocality", "") or "").strip().lower()
    return ""


def extraire_code_postal(item):
    """Extrait le code postal depuis schema:address."""
    loc = item.get("isLocatedAt", {})
    if isinstance(loc, list):
        loc = loc[0]
    addr = loc.get("schema:address", {}) if isinstance(loc, dict) else {}
    if isinstance(addr, list):
        addr = addr[0]
    if isinstance(addr, dict):
        return str(addr.get("schema:postalCode", "") or "").strip()
    return ""


def extraire_categorie(item):
    """Determine la categorie normalisee depuis les types DATAtourisme."""
    types = item.get("@type", [])
    if isinstance(types, str):
        types = [types]

    # Passage 1 : correspondance directe
    for t in types:
        t_clean = t.split(":")[-1].split("#")[-1]
        if t_clean in CATEGORIES:
            return CATEGORIES[t_clean], t_clean

    # Passage 2 : correspondance par sous-chaine
    for t in types:
        t_lower = t.lower()
        for key, val in CATEGORIES.items():
            if key.lower() in t_lower:
                return val, key

    return "Autre", "PointOfInterest"


def extraire_telephone(item):
    """Extrait le premier numero de telephone disponible."""
    contact = item.get("hasContact", [])
    if isinstance(contact, list) and contact:
        contact = contact[0]
    if isinstance(contact, dict):
        tel = contact.get("schema:telephone", "") or contact.get("foaf:phone", "")
        return str(tel).strip()[:50] if tel else None
    return None


def extraire_site_web(item):
    """Extrait l'URL du site web."""
    contact = item.get("hasContact", [])
    if isinstance(contact, list) and contact:
        contact = contact[0]
    if isinstance(contact, dict):
        url = contact.get("foaf:homepage", "") or contact.get("schema:url", "")
        return str(url).strip()[:500] if url else None
    return None


def extraire_date_maj(item):
    """Extrait la date de derniere mise a jour."""
    date = item.get("lastUpdate") or item.get("dc:date")
    if date:
        try:
            return pd.to_datetime(str(date))
        except Exception:
            pass
    return None


# -- Etape 3 : Extraction Silver -----------------------------------------------

print("\nExtraction et normalisation des champs...")

pois_silver = []
erreurs     = 0

for item in graph:
    try:
        nom = extraire_nom(item)
        if not nom or len(nom) < 2:
            continue

        lat, lon = extraire_coordonnees(item)
        if not lat or not lon or lat == 0 or lon == 0:
            continue

        # Filtre geographique Pays de la Loire
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            continue

        categorie, sous_cat = extraire_categorie(item)
        commune             = extraire_commune(item)
        code_postal         = extraire_code_postal(item)
        telephone           = extraire_telephone(item)
        site_web            = extraire_site_web(item)
        date_maj            = extraire_date_maj(item)

        pois_silver.append({
            "nom"           : nom[:500],
            "categorie"     : categorie,
            "sous_categorie": sous_cat[:100] if sous_cat else None,
            "commune"       : commune[:100],
            "code_postal"   : code_postal[:10],
            "latitude"      : lat,
            "longitude"     : lon,
            "telephone"     : telephone,
            "site_web"      : site_web,
            "region"        : "Pays de la Loire",
            "source"        : "datatourisme",
            "date_maj"      : date_maj,
        })
    except Exception:
        erreurs += 1
        continue

print(f"  {len(pois_silver)} POI extraits ({erreurs} erreurs ignorees)")

df_silver = pd.DataFrame(pois_silver)
avant     = len(df_silver)
df_silver = df_silver.drop_duplicates(subset=["nom", "commune"])
print(f"  Doublons supprimes : {avant} -> {len(df_silver)}")

print("\n  Repartition par categorie :")
print(df_silver["categorie"].value_counts().to_string())


# -- Calcul du score de popularite (0-10) --------------------------------------
# Le score sert au modele KNN comme feature de qualite du POI.
# Source des donnees : uniquement ce qu'on a dans DATAtourisme.

print("\nCalcul du score de popularite...")

seuil_rare      = 0.05 * len(df_silver)  # categorie < 5% du total = categorie rare
cat_counts      = df_silver["categorie"].value_counts()
cats_rares      = set(cat_counts[cat_counts < seuil_rare].index)
date_limite_maj = datetime.now() - timedelta(days=180)


def calculer_score(row):
    """
    Calcule un score de popularite synthetique de 0 a 10.
    Criteres positifs : presence de contacts, fraicheur des donnees, rarete de categorie.
    """
    score = 0.0
    if pd.notna(row.get("site_web"))  and row["site_web"]:
        score += 3.0
    if pd.notna(row.get("telephone")) and row["telephone"]:
        score += 2.0
    if row.get("categorie") in cats_rares:
        # Valorise les POI dans des categories peu representees (Culture, Nature, etc.)
        score += 2.0
    if pd.notna(row.get("date_maj")):
        try:
            if pd.to_datetime(row["date_maj"]).replace(tzinfo=None) > date_limite_maj:
                score += 3.0
        except Exception:
            pass
    return round(min(score, 10.0), 2)


df_silver["note_moyenne"] = df_silver.apply(calculer_score, axis=1)

# Normalisation 0-10
score_max = df_silver["note_moyenne"].max()
if score_max > 0:
    df_silver["note_moyenne"] = (df_silver["note_moyenne"] / score_max * 10).round(2)

print(f"  Score moyen : {df_silver['note_moyenne'].mean():.2f} / 10")
print(f"  POI avec score > 0 : {(df_silver['note_moyenne'] > 0).sum()}")


# -- Etape 4 : Insertion Silver ------------------------------------------------

print("\nInsertion dans silver.poi...")
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE silver.poi RESTART IDENTITY CASCADE"))
    records_s = []
    for _, row in df_silver.iterrows():
        records_s.append({
            "nom" : row["nom"],
            "cat" : row["categorie"],
            "scat": row["sous_categorie"] if pd.notna(row["sous_categorie"]) else None,
            "com" : row["commune"] if pd.notna(row["commune"]) else None,
            "cp"  : row["code_postal"] if pd.notna(row["code_postal"]) else None,
            "dep" : None,
            "lat" : float(row["latitude"]) if pd.notna(row["latitude"]) else None,
            "lon" : float(row["longitude"]) if pd.notna(row["longitude"]) else None,
            "tel" : row["telephone"] if pd.notna(row["telephone"]) else None,
            "web" : row["site_web"] if pd.notna(row["site_web"]) else None,
            "note": float(row["note_moyenne"]) if pd.notna(row["note_moyenne"]) else 0.0,
            "reg" : row["region"] if pd.notna(row["region"]) else None,
            "src" : row["source"],
            "dmaj": row["date_maj"] if pd.notna(row["date_maj"]) else None,
        })
    
    # Bulk insert
    batch_size = 1000
    for i in range(0, len(records_s), batch_size):
        batch = records_s[i:i+batch_size]
        conn.execute(text("""
            INSERT INTO silver.poi
              (nom, categorie, sous_categorie, commune, code_postal, departement,
               latitude, longitude, telephone, site_web, note_moyenne,
               region, source, date_maj)
            VALUES (:nom, :cat, :scat, :com, :cp, :dep, :lat, :lon,
                    :tel, :web, :note, :reg, :src, :dmaj)
        """), batch)
    conn.commit()

nb = pd.read_sql("SELECT COUNT(*) as n FROM silver.poi", engine).iloc[0]["n"]
print(f"  {nb} POI dans silver.poi")

print("\nScript 02 termine.")
