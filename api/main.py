"""API Wandrail - couche de donnees pour le front React.

Expose en lecture les donnees touristiques de l'architecture Medaillon
(schemas silver / gold) deja construite pour l'app Streamlit.

Lancement local :
    cd api
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Documentation interactive : http://localhost:8000/docs
"""
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from db import engine

app = FastAPI(
    title="Wandrail API",
    description="Donnees tourisme en train - Pays de la Loire",
    version="0.1.0",
)

# ── CORS : autoriser le front (dev Vite + prod) ────────────────────
origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────
def rows_to_dicts(result):
    """Convertit un resultat SQLAlchemy en liste de dictionnaires."""
    cols = result.keys()
    return [dict(zip(cols, row)) for row in result.fetchall()]


# ── Endpoints ──────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    """Verifie que l'API et la base repondent."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as exc:
        return {"status": "ok", "db": "error", "detail": str(exc)}


@app.get("/api/stats")
def stats():
    """Chiffres cles affiches sur la page d'accueil."""
    sql = text(
        """
        SELECT
          (SELECT COUNT(*) FROM silver.gares WHERE latitude IS NOT NULL) AS nb_gares,
          (SELECT COUNT(*) FROM silver.poi) AS nb_lieux,
          (SELECT COUNT(DISTINCT departement) FROM silver.gares
             WHERE departement IS NOT NULL) AS nb_departements
        """
    )
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
    return {
        "nb_gares": row[0],
        "nb_lieux": row[1],
        "nb_departements": row[2],
        "co2_vs_voiture_pct": 91,
        "nb_profils": 5,
    }


@app.get("/api/departements")
def departements():
    """Liste des departements (pour les filtres)."""
    sql = text(
        """
        SELECT DISTINCT departement FROM silver.gares
        WHERE departement IS NOT NULL ORDER BY departement
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()
    return [r[0] for r in rows]


@app.get("/api/profils")
def profils():
    """Liste des profils touristiques distincts (pour les filtres)."""
    sql = text(
        """
        SELECT DISTINCT profil_touristique FROM gold.dim_gare
        WHERE profil_touristique IS NOT NULL ORDER BY profil_touristique
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()
    return [r[0] for r in rows]


@app.get("/api/destinations")
def destinations(
    q: str | None = Query(None, description="Recherche commune ou gare"),
    departement: str | None = None,
    profil: str | None = None,
    min_score: float = 0.0,
    sort: str = Query("score", pattern="^(score|nom|poi)$"),
    limit: int = Query(60, ge=1, le=500),
):
    """Liste filtrable des destinations (gares enrichies)."""
    clauses = [
        "g.latitude IS NOT NULL",
        "d.score_attractivite IS NOT NULL",
        "d.score_attractivite >= :min_score",
    ]
    params = {"min_score": min_score, "limit": limit}

    if q:
        clauses.append("(g.commune ILIKE :q OR g.nom_gare ILIKE :q)")
        params["q"] = f"%{q}%"
    if departement:
        clauses.append("g.departement = :departement")
        params["departement"] = departement
    if profil:
        clauses.append("d.profil_touristique = :profil")
        params["profil"] = profil

    order = {
        "score": "d.score_attractivite DESC",
        "nom": "g.commune ASC",
        "poi": "d.nb_poi_5km DESC",
    }[sort]

    sql = text(
        f"""
        SELECT g.nom_gare, g.commune, g.departement, g.latitude, g.longitude,
               d.score_attractivite, d.profil_touristique,
               d.nb_poi_5km, d.nb_categories
        FROM silver.gares g
        LEFT JOIN gold.dim_gare d ON d.code_uic = g.code_uic
        WHERE {" AND ".join(clauses)}
        ORDER BY {order}
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        return rows_to_dicts(conn.execute(sql, params))


@app.get("/api/destinations/{nom_gare}")
def destination_detail(nom_gare: str, rayon: float = Query(10.0, ge=0.5, le=50)):
    """Detail d'une destination + lieux a proximite de la gare."""
    sql_dest = text(
        """
        SELECT g.nom_gare, g.commune, g.departement, g.latitude, g.longitude,
               d.score_attractivite, d.profil_touristique,
               d.nb_poi_5km, d.nb_categories
        FROM silver.gares g
        LEFT JOIN gold.dim_gare d ON d.code_uic = g.code_uic
        WHERE g.nom_gare = :nom
        LIMIT 1
        """
    )
    sql_poi = text(
        """
        SELECT p.nom, p.categorie, p.commune, p.latitude, p.longitude,
               p.note_moyenne, pe.distance_gare_km, pe.temps_marche_min
        FROM silver.poi p
        JOIN silver.poi_enrichi pe ON pe.id_poi = p.id
        WHERE pe.nom_gare = :nom AND pe.distance_gare_km <= :rayon
          AND p.latitude IS NOT NULL
        ORDER BY pe.distance_gare_km
        LIMIT 300
        """
    )
    with engine.connect() as conn:
        result = conn.execute(sql_dest, {"nom": nom_gare})
        cols = result.keys()
        dest_row = result.fetchone()
        if dest_row is None:
            raise HTTPException(status_code=404, detail="Destination introuvable")
        dest = dict(zip(cols, dest_row))
        pois = rows_to_dicts(conn.execute(sql_poi, {"nom": nom_gare, "rayon": rayon}))
    return {"destination": dest, "pois": pois}
