"""
Script 09 - Evenements culturels via OpenAgenda (Pays de la Loire)
------------------------------------------------------------------
OpenAgenda est une plateforme open data d'evenements culturels.
L'API est gratuite avec inscription (cle publique disponible librement).

Ce script :
  1. Recupere les evenements a venir en PDL via l'API OpenAgenda
  2. Filtre sur les evenements avec coordonnees GPS
  3. Insere dans silver.evenements

Inscription : https://openagenda.com/developers
La cle publique est disponible dans votre compte OpenAgenda.
Ajouter dans .env : OPENAGENDA_API_KEY=votre_cle

Sans cle : le script utilise une cle publique de demonstration (limite 100 req/h).
"""

import sys
import os
import requests
import pandas as pd
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


engine    = get_engine()
OA_KEY    = os.getenv("OPENAGENDA_API_KEY", "")

# UIDs des agendas OpenAgenda pour les departements PDL
# Ces agendas sont publics et contiennent les evenements locaux.
AGENDAS_PDL = {
    "Loire-Atlantique (44)"  : "68155026",
    "Maine-et-Loire (49)"    : "68156202",
    "Vendee (85)"            : "68156340",
    "Sarthe (72)"            : "68156270",
    "Mayenne (53)"           : "68156100",
}

# On recupere les evenements sur les 6 prochains mois
DATE_DEBUT = datetime.now().strftime("%Y-%m-%d")
DATE_FIN   = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")

# Bounding box PDL pour filtrer les resultats
LAT_MIN, LAT_MAX = 46.3, 48.4
LON_MIN, LON_MAX = -2.6,  1.0


print("=" * 60)
print("SCRIPT 09 - Evenements OpenAgenda Pays de la Loire")
print("=" * 60)


def appeler_openagenda(agenda_uid: str, cle: str, after: str, before: str, size: int = 100) -> list:
    """
    Appelle l'API OpenAgenda pour un agenda donne.
    Retourne la liste des evenements ou une liste vide en cas d'erreur.
    """
    url    = f"https://api.openagenda.com/v2/agendas/{agenda_uid}/events"
    params = {
        "key"         : cle,
        "size"        : size,
        "after[0]"    : after,
        "before[0]"   : before,
        "relative[0]" : "current",
        "relative[1]" : "upcoming",
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("events", [])
    except Exception as e:
        print(f"    Erreur OpenAgenda agenda {agenda_uid} : {e}")
        return []


if not OA_KEY:
    print("\nAucune cle OpenAgenda trouvee dans .env (OPENAGENDA_API_KEY).")
    print("Le script va generer des donnees d'exemple pour les tests.")
    print("Inscription gratuite : https://openagenda.com/developers")

    # Donnees d'exemple pour les tests locaux
    EXEMPLES = [
        {"nom": "Festival Loire en Scene", "type_event": "Festival", "commune": "nantes",
         "latitude": 47.2178, "longitude": -1.5420,
         "date_debut": "2026-07-15", "date_fin": "2026-07-20", "gratuit": False,
         "url": "https://openagenda.com"},
        {"nom": "Journees du Patrimoine", "type_event": "Patrimoine", "commune": "angers",
         "latitude": 47.4637, "longitude": -0.5507,
         "date_debut": "2026-09-20", "date_fin": "2026-09-21", "gratuit": True,
         "url": "https://journeesdupatrimoine.culture.gouv.fr"},
        {"nom": "Marche de Noel du Mans", "type_event": "Marche", "commune": "le mans",
         "latitude": 48.0028, "longitude": 0.1928,
         "date_debut": "2026-12-01", "date_fin": "2026-12-24", "gratuit": True,
         "url": "https://openagenda.com"},
        {"nom": "Fete de la Musique en Vendee", "type_event": "Concert", "commune": "la roche-sur-yon",
         "latitude": 46.6702, "longitude": -1.4261,
         "date_debut": "2026-06-21", "date_fin": "2026-06-21", "gratuit": True,
         "url": "https://openagenda.com"},
        {"nom": "Festival Interceltique", "type_event": "Festival", "commune": "nantes",
         "latitude": 47.2178, "longitude": -1.5420,
         "date_debut": "2026-08-01", "date_fin": "2026-08-10", "gratuit": False,
         "url": "https://openagenda.com"},
    ]

    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE silver.evenements RESTART IDENTITY"))
        for ev in EXEMPLES:
            conn.execute(text("""
                INSERT INTO silver.evenements
                  (nom, type_event, commune, latitude, longitude,
                   date_debut, date_fin, gratuit, url)
                VALUES (:nom, :type, :com, :lat, :lon, :dd, :df, :gr, :url)
            """), {
                "nom" : ev["nom"],
                "type": ev["type_event"],
                "com" : ev["commune"],
                "lat" : ev["latitude"],
                "lon" : ev["longitude"],
                "dd"  : ev["date_debut"],
                "df"  : ev["date_fin"],
                "gr"  : ev["gratuit"],
                "url" : ev["url"],
            })
        conn.commit()

    print(f"\n  {len(EXEMPLES)} evenements d'exemple inseres dans silver.evenements")
    print("  Relancer ce script apres avoir ajoute OPENAGENDA_API_KEY dans .env")
    print("\nScript 09 termine (mode demonstration).")
    sys.exit(0)


# -- Mode API OpenAgenda -------------------------------------------------------

print(f"\nPeriode : {DATE_DEBUT} -> {DATE_FIN}")
print(f"Agendas PDL : {len(AGENDAS_PDL)}")

tous_evenements = []

for nom_agenda, uid in AGENDAS_PDL.items():
    print(f"\n  Agenda : {nom_agenda} (uid={uid})")
    events = appeler_openagenda(uid, OA_KEY, DATE_DEBUT, DATE_FIN, size=200)
    print(f"    {len(events)} evenements recuperes")

    for ev in events:
        try:
            # Coordonnees GPS
            location = ev.get("location", {})
            lat = location.get("latitude")
            lon = location.get("longitude")

            if not lat or not lon:
                continue

            # Filtre geographique PDL
            if not (LAT_MIN <= float(lat) <= LAT_MAX and LON_MIN <= float(lon) <= LON_MAX):
                continue

            # Nom de l'evenement
            titre = ev.get("title", {})
            nom   = titre.get("fr", titre.get("en", "Evenement sans nom"))

            # Dates
            timings = ev.get("timings", [{}])
            if timings:
                date_debut = timings[0].get("begin", "")[:10]
                date_fin   = timings[-1].get("end", date_debut)[:10]
            else:
                date_debut = ""
                date_fin   = ""

            # Gratuit
            conditions = ev.get("conditions", {})
            gratuit    = not conditions or conditions.get("fr", "").lower() in ["", "gratuit", "free"]

            # URL
            url = f"https://openagenda.com/agendas/{uid}/events/{ev.get('uid', '')}"

            # Categorie
            keywords = ev.get("keywords", {}).get("fr", [])
            if isinstance(keywords, str):
                keywords = [keywords]
            type_event = keywords[0] if keywords else "Autre"

            tous_evenements.append({
                "nom"       : str(nom)[:500],
                "type_event": str(type_event)[:100],
                "commune"   : str(location.get("city", "")).lower()[:100],
                "latitude"  : float(lat),
                "longitude" : float(lon),
                "date_debut": date_debut or None,
                "date_fin"  : date_fin or None,
                "gratuit"   : bool(gratuit),
                "url"       : url[:500],
            })

        except Exception:
            continue

print(f"\n  Total : {len(tous_evenements)} evenements PDL extraits")

# Deduplication sur nom + date
df_ev = pd.DataFrame(tous_evenements)
avant = len(df_ev)
df_ev = df_ev.drop_duplicates(subset=["nom", "date_debut"])
print(f"  Apres deduplication : {len(df_ev)} evenements (suppression de {avant - len(df_ev)} doublons)")


# -- Insertion en base ---------------------------------------------------------

print("\nInsertion dans silver.evenements...")
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE silver.evenements RESTART IDENTITY"))
    for _, row in df_ev.iterrows():
        conn.execute(text("""
            INSERT INTO silver.evenements
              (nom, type_event, commune, latitude, longitude,
               date_debut, date_fin, gratuit, url)
            VALUES (:nom, :type, :com, :lat, :lon, :dd, :df, :gr, :url)
        """), {
            "nom" : row["nom"],
            "type": row["type_event"],
            "com" : row["commune"],
            "lat" : row["latitude"],
            "lon" : row["longitude"],
            "dd"  : row["date_debut"] or None,
            "df"  : row["date_fin"] or None,
            "gr"  : bool(row["gratuit"]),
            "url" : row["url"],
        })
    conn.commit()

print(f"  {len(df_ev)} evenements dans silver.evenements")
print("\nScript 09 termine.")
