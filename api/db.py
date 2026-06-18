"""Connexion a la base PostgreSQL / Supabase.

On reutilise la meme chaine DATABASE_URL que l'application Streamlit.
La valeur reelle vient du fichier .env (jamais commite) ou des variables
d'environnement du service cloud (Render, Railway, etc.).
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:00000@localhost:5434/tourisme_train",
)

# On utilise le driver psycopg v3 (wheels disponibles jusqu'a Python 3.14).
# On reecrit le schema de l'URL pour que SQLAlchemy choisisse psycopg v3,
# quelle que soit la forme fournie (postgres:// ou postgresql://).
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://"):]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]

# pool_pre_ping evite les connexions mortes (le pooler Supabase coupe les
# connexions inactives). pool_recycle force le renouvellement avant timeout.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
)
