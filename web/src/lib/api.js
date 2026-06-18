// Client API minimaliste vers le backend FastAPI.
// En dev : VITE_API_BASE vide -> Vite proxy /api vers localhost:8000.
// En prod : VITE_API_BASE = URL publique de l'API.

const BASE = import.meta.env.VITE_API_BASE || ''

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    throw new Error(`Erreur API ${res.status} sur ${path}`)
  }
  return res.json()
}

export const api = {
  stats: () => get('/api/stats'),
  departements: () => get('/api/departements'),
  profils: () => get('/api/profils'),
  destinations: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v != null),
    ).toString()
    return get(`/api/destinations${qs ? `?${qs}` : ''}`)
  },
  destination: (nom, rayon) =>
    get(`/api/destinations/${encodeURIComponent(nom)}${rayon ? `?rayon=${rayon}` : ''}`),
}
