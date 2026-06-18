import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import DestinationCard from '../components/DestinationCard'
import { SkeletonGrid } from '../components/CardSkeleton'

export default function Destinations() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [deps, setDeps] = useState([])
  const [profils, setProfils] = useState([])
  const [dests, setDests] = useState([])
  const [loading, setLoading] = useState(true)

  const q = searchParams.get('q') || ''
  const departement = searchParams.get('departement') || ''
  const profil = searchParams.get('profil') || ''
  const sort = searchParams.get('sort') || 'score'
  const hasFilters = q || departement || profil || sort !== 'score'

  // Met a jour un parametre d'URL (et nettoie les valeurs vides)
  const setParam = (key, value) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next)
  }

  useEffect(() => {
    api.departements().then(setDeps).catch(() => {})
    api.profils().then(setProfils).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    api
      .destinations({ q, departement, profil, sort, limit: 60 })
      .then(setDests)
      .catch(() => setDests([]))
      .finally(() => setLoading(false))
  }, [q, departement, profil, sort])

  return (
    <div className="mx-auto max-w-page px-6 py-10">
      <h1 className="text-3xl font-black tracking-tighter text-ink">Toutes les destinations</h1>
      <p className="mt-1 text-sm text-muted">
        Filtrez par departement, profil ou recherchez une ville.
      </p>

      {/* Barre de filtres */}
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <input
          value={q}
          onChange={(e) => setParam('q', e.target.value)}
          placeholder="Rechercher une ville..."
          className="h-11 min-w-[220px] flex-1 rounded-xl border-[1.5px] border-black/15 bg-neutral-50 px-4 text-sm outline-none focus:border-violet"
        />
        <select
          value={departement}
          onChange={(e) => setParam('departement', e.target.value)}
          className="h-11 rounded-xl border-[1.5px] border-black/15 bg-white px-3 text-sm outline-none focus:border-violet"
        >
          <option value="">Tous departements</option>
          {deps.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <select
          value={profil}
          onChange={(e) => setParam('profil', e.target.value)}
          className="h-11 rounded-xl border-[1.5px] border-black/15 bg-white px-3 text-sm outline-none focus:border-violet"
        >
          <option value="">Tous profils</option>
          {profils.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => setParam('sort', e.target.value)}
          className="h-11 rounded-xl border-[1.5px] border-black/15 bg-white px-3 text-sm outline-none focus:border-violet"
        >
          <option value="score">Tri : Score</option>
          <option value="nom">Tri : Nom</option>
          <option value="poi">Tri : Nb activites</option>
        </select>
        {hasFilters && (
          <button
            onClick={() => setSearchParams({})}
            className="h-11 rounded-xl px-3 text-sm font-semibold text-violet hover:underline"
          >
            Reinitialiser
          </button>
        )}
      </div>

      {/* Resultats */}
      <div className="mb-6 mt-8 text-sm font-semibold text-ink">
        {loading ? 'Recherche en cours...' : `${dests.length} destination${dests.length > 1 ? 's' : ''}`}
      </div>

      {loading ? (
        <SkeletonGrid count={6} />
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {dests.map((d) => (
            <DestinationCard key={d.nom_gare} dest={d} />
          ))}
        </div>
      )}

      {!loading && dests.length === 0 && (
        <div className="py-20 text-center text-muted">
          Aucune destination ne correspond a ces criteres.
        </div>
      )}
    </div>
  )
}
