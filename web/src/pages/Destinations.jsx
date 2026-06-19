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

  const selCls =
    'h-11 w-full rounded-xl border-[1.5px] border-black/15 bg-white px-3 text-sm outline-none focus:border-violet'

  return (
    <div className="mx-auto max-w-page px-6 py-10">
      <h1 className="text-3xl font-black tracking-tighter text-ink">Toutes les destinations</h1>
      <p className="mt-1 text-sm text-muted">Filtrez par departement, profil ou recherchez une ville.</p>

      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-[260px_1fr]">
        {/* Filtres - colonne laterale */}
        <aside className="h-fit space-y-5 rounded-2xl border border-line bg-white p-5 shadow-card lg:sticky lg:top-20">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-black uppercase tracking-wide text-ink">Filtres</h2>
            {hasFilters && (
              <button
                onClick={() => setSearchParams({})}
                className="text-xs font-semibold text-violet hover:underline"
              >
                Reinitialiser
              </button>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-muted">Recherche</label>
            <input
              value={q}
              onChange={(e) => setParam('q', e.target.value)}
              placeholder="Une ville..."
              className="h-11 w-full rounded-xl border-[1.5px] border-black/15 bg-neutral-50 px-4 text-sm outline-none focus:border-violet"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-muted">Departement</label>
            <select value={departement} onChange={(e) => setParam('departement', e.target.value)} className={selCls}>
              <option value="">Tous les departements</option>
              {deps.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-muted">Profil touristique</label>
            <select value={profil} onChange={(e) => setParam('profil', e.target.value)} className={selCls}>
              <option value="">Tous les profils</option>
              {profils.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-muted">Trier par</label>
            <select value={sort} onChange={(e) => setParam('sort', e.target.value)} className={selCls}>
              <option value="score">Score d'attractivite</option>
              <option value="nom">Nom (A-Z)</option>
              <option value="poi">Nombre d'activites</option>
            </select>
          </div>
        </aside>

        {/* Resultats */}
        <div>
          <div className="mb-5 text-sm font-semibold text-ink">
            {loading ? 'Recherche en cours...' : `${dests.length} destination${dests.length > 1 ? 's' : ''}`}
          </div>

          {loading ? (
            <SkeletonGrid count={6} />
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
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
      </div>
    </div>
  )
}
