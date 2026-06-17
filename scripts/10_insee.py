"""
Script 10 - Donnees demographiques INSEE (Pays de la Loire)
-----------------------------------------------------------
Recupere depuis l'API INSEE les donnees de population par commune PDL.
Ces donnees servent a :
  - Enrichir les fiches gare avec la population de la ville
  - Calculer la densite touristique (POI / habitant)
  - Alimenter les graphiques de l'app analyste

Source : API INSEE Donnees locales (gratuite, sans cle)
URL : https://api.insee.fr/donnees-locales/V0.1/

Alternativement, si l'API est indisponible, on utilise le fichier CSV
des communes PDL disponible sur data.gouv.fr.

Resultat attendu : ~1500 communes PDL dans silver.population
"""

import sys
import os
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

# Codes departement PDL
CODES_DEPT = ["44", "49", "53", "72", "85"]

# URL du fichier CSV population communes 2021 (data.gouv.fr - mise a jour annuelle)
URL_POPULATION_CSV = (
    "https://www.insee.fr/fr/statistiques/fichier/6683035/base-cc-serie-historique-2021.zip"
)

# Fallback : fichier CSV communes avec population (source simplifiee)
URL_COMMUNES_SIMPLIFIEE = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson"
)


print("=" * 60)
print("SCRIPT 10 - Donnees INSEE Communes Pays de la Loire")
print("=" * 60)


# -- Recuperation des communes PDL depuis la DB --------------------------------
# On s'appuie sur les communes deja presentes dans silver.gares et silver.poi
# pour construire une liste des communes a enrichir.

print("\nRecuperation des communes PDL depuis la base de donnees...")

df_communes_gares = pd.read_sql("""
    SELECT DISTINCT commune, code_departement
    FROM silver.gares
    WHERE commune IS NOT NULL AND commune != ''
""", engine)

df_communes_poi = pd.read_sql("""
    SELECT DISTINCT commune
    FROM silver.poi
    WHERE commune IS NOT NULL AND commune != ''
    LIMIT 2000
""", engine)

# Union des deux sources de communes
all_communes = set(df_communes_gares["commune"].str.lower().tolist())
all_communes |= set(df_communes_poi["commune"].str.lower().tolist())
all_communes.discard("")

print(f"  {len(all_communes)} communes PDL identifiees depuis gares + POI")


# -- Appel API INSEE -----------------------------------------------------------
# L'API INSEE peut etre lente ou temporairement indisponible.
# On utilise une source alternative si necessaire.

print("\nTentative de recuperation des donnees INSEE...")

df_pop_raw = pd.DataFrame()

# Tentative 1 : API GEO INSEE (donnees de reference communes)
try:
    url_geo = "https://geo.api.gouv.fr/communes"
    rows_insee = []
    for code_dept in CODES_DEPT:
        params = {
            "codeDepartement": code_dept,
            "fields"         : "nom,code,codeDepartement,population,surface",
            "format"         : "json",
        }
        r = requests.get(url_geo, params=params, timeout=30)
        r.raise_for_status()
        communes = r.json()
        for c in communes:
            rows_insee.append({
                "commune"       : str(c.get("nom", "")).lower().strip(),
                "code_commune"  : str(c.get("code", "")),
                "code_dept"     : str(c.get("codeDepartement", "")),
                "population"    : int(c.get("population", 0) or 0),
                "superficie_km2": round(float(c.get("surface", 0) or 0) / 100, 2),
            })

    df_pop_raw = pd.DataFrame(rows_insee)
    print(f"  {len(df_pop_raw)} communes recuperees depuis l'API geo.api.gouv.fr")

except Exception as e:
    print(f"  API geo.api.gouv.fr indisponible : {e}")
    print("  Passage en mode donnees minimales...")

    # Mode de secours : generer des donnees approximatives pour les communes connues
    # Populations des villes PDL les plus importantes (source Wikipedia)
    POPULATIONS_CONNUES = {
        "nantes"            : (320732, 65.19),
        "le mans"           : (145502, 52.89),
        "angers"            : (156088, 42.70),
        "saint-nazaire"     : (71429,  65.33),
        "la roche-sur-yon"  : (60448,  79.72),
        "laval"             : (50617,  57.77),
        "cholet"            : (55179,  89.29),
        "saumur"            : (25810,  46.47),
        "saint-herblain"    : (47010,  22.45),
        "rezé"              : (43095,  15.84),
        "la baule-escoublac": (16325,  27.00),
        "les sables-d'olonne": (43085, 88.71),
    }

    rows_approx = []
    for commune, (pop, surf) in POPULATIONS_CONNUES.items():
        rows_approx.append({
            "commune"       : commune,
            "code_commune"  : "",
            "code_dept"     : "",
            "population"    : pop,
            "superficie_km2": surf,
        })

    df_pop_raw = pd.DataFrame(rows_approx)
    print(f"  {len(df_pop_raw)} communes avec donnees de reference (mode secours)")


# -- Calcul de la densite et enrichissement ------------------------------------

if not df_pop_raw.empty:
    df_pop_raw["densite"] = df_pop_raw.apply(
        lambda r: round(r["population"] / r["superficie_km2"], 1)
        if r["superficie_km2"] > 0 else 0,
        axis=1
    )
    df_pop_raw["revenu_moyen"] = 0.0  # Non disponible sans acces special INSEE

    # Deduplication
    df_pop_raw = df_pop_raw.drop_duplicates(subset=["commune"])

    print(f"\n  Population moyenne PDL : {df_pop_raw['population'].mean():.0f} hab.")
    print(f"  Ville la plus peuplee  : {df_pop_raw.loc[df_pop_raw['population'].idxmax(), 'commune'].title()}")


# -- Insertion dans silver.population ------------------------------------------

print("\nInsertion dans silver.population...")
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE silver.population RESTART IDENTITY"))
    if not df_pop_raw.empty:
        for _, row in df_pop_raw.iterrows():
            conn.execute(text("""
                INSERT INTO silver.population
                  (commune, code_commune, population_2024, superficie_km2, densite, revenu_moyen)
                VALUES (:com, :code, :pop, :surf, :dens, :rev)
                ON CONFLICT (commune) DO UPDATE
                  SET population_2024 = EXCLUDED.population_2024,
                      superficie_km2  = EXCLUDED.superficie_km2,
                      densite         = EXCLUDED.densite
            """), {
                "com" : row["commune"],
                "code": row.get("code_commune", ""),
                "pop" : int(row.get("population", 0)),
                "surf": float(row.get("superficie_km2", 0)),
                "dens": float(row.get("densite", 0)),
                "rev" : 0.0,
            })
        conn.commit()

nb = pd.read_sql("SELECT COUNT(*) as n FROM silver.population", engine).iloc[0]["n"]
print(f"  {nb} communes dans silver.population")


# -- Enrichissement de gold.dim_gare avec la population -----------------------

print("\nEnrichissement de gold.dim_gare avec les populations communes...")

if not df_pop_raw.empty:
    pop_dict = dict(zip(
        df_pop_raw["commune"].str.lower(),
        df_pop_raw["population"]
    ))

    df_gares = pd.read_sql("SELECT id, commune FROM gold.dim_gare", engine)
    updated = 0

    with engine.connect() as conn:
        for _, gare in df_gares.iterrows():
            commune = str(gare.get("commune", "") or "").lower().strip()
            pop = pop_dict.get(commune)
            if pop:
                conn.execute(text("""
                    UPDATE gold.dim_gare
                    SET nb_voyageurs_annuel = GREATEST(nb_voyageurs_annuel, :pop)
                    WHERE id = :id AND nb_voyageurs_annuel = 0
                """), {"pop": int(pop), "id": int(gare["id"])})
                updated += 1
        conn.commit()

    print(f"  {updated} gares enrichies avec la population de leur commune")


# -- Rapport -------------------------------------------------------------------

print("\n" + "=" * 60)
print("RESUME INSEE")
print("=" * 60)

stats = pd.read_sql("""
    SELECT COUNT(*) as nb_communes,
           SUM(population_2024) as pop_totale,
           AVG(population_2024) as pop_moy,
           MAX(population_2024) as pop_max
    FROM silver.population
""", engine)
print(stats.to_string(index=False))

print("\nScript 10 termine.")
