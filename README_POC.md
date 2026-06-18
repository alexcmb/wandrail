# Wandrail - POC front React + API FastAPI

Nouvelle interface du projet Wandrail, en remplacement de Streamlit pour la
partie publique (vitrine touristique). L'app Streamlit existante (`app/`) reste
intacte et fonctionnelle.

## Architecture

```
web/  (React + Vite + Tailwind)  -->  api/  (FastAPI)  -->  Supabase / PostgreSQL
   front, deployable sur Vercel       couche data Python        base inchangee
```

- **`api/`** : API REST en Python (FastAPI). Reutilise la meme connexion
  `DATABASE_URL` que Streamlit. Expose en lecture les destinations, les lieux
  (POI), les stats et les filtres.
- **`web/`** : front React. Aucun identifiant de base cote navigateur :
  il ne parle qu'a l'API.

## 1. Lancer l'API (terminal 1)

```bash
cd api
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env         # puis renseigner DATABASE_URL
uvicorn main:app --reload --port 8000
```

Verifier : http://localhost:8000/docs (documentation interactive Swagger).

## 2. Lancer le front (terminal 2)

```bash
cd web
npm install
npm run dev
```

Ouvrir http://localhost:5173. En dev, Vite redirige automatiquement les appels
`/api/*` vers le backend sur le port 8000 (voir `vite.config.js`), donc aucune
config supplementaire n'est necessaire.

## 3. Deploiement cloud

### Front (Vercel ou Netlify)
- Importer le repo, definir le dossier racine sur `web/`.
- Commande de build : `npm run build` - dossier de sortie : `dist`.
- Variable d'environnement : `VITE_API_BASE` = URL publique de l'API.
- `web/vercel.json` gere deja les routes profondes (SPA).

### API (Render, Railway ou Fly.io)
- Dossier racine : `api/`.
- Commande de demarrage :
  `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Variables d'environnement :
  - `DATABASE_URL` : la chaine Supabase (jamais commitee).
  - `CORS_ORIGINS` : l'URL Vercel du front.

## Endpoints disponibles

| Methode | Route | Description |
|--------|-------|-------------|
| GET | `/api/health` | Etat API + base |
| GET | `/api/stats` | Chiffres cles (accueil) |
| GET | `/api/departements` | Liste des departements |
| GET | `/api/profils` | Profils touristiques |
| GET | `/api/destinations` | Liste filtrable (`q`, `departement`, `profil`, `min_score`, `sort`, `limit`) |
| GET | `/api/destinations/{nom_gare}` | Detail + lieux a proximite |

## Securite

- Les secrets (`.env`) ne sont jamais commites (voir `.gitignore`).
- Le navigateur ne voit jamais la base : tout passe par l'API.
- L'API est en lecture seule pour ce POC (methodes GET uniquement).
