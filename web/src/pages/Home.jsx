import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import DestinationCard from '../components/DestinationCard'
import { SkeletonGrid } from '../components/CardSkeleton'
import CategoryChips from '../components/CategoryChips'
import ProfilCard from '../components/ProfilCard'
import { HERO_IMAGE } from '../lib/images'

const PROFILS = [
  { nom: 'Famille', desc: 'Parcs, activites enfants, nature, grands espaces' },
  { nom: 'Solo', desc: 'Culture, patrimoine, aventure en liberte' },
  { nom: 'Couple', desc: 'Gastronomie, charme, romantisme, detente' },
  { nom: 'Groupe', desc: 'Sport, evenements, animation, fun collectif' },
  { nom: 'Eco', desc: 'Nature, mobilite douce, empreinte minimale' },
]

export default function Home() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [deps, setDeps] = useState([])
  const [dests, setDests] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [dep, setDep] = useState('')

  useEffect(() => {
    api.stats().then(setStats).catch(() => {})
    api.departements().then(setDeps).catch(() => {})
    api
      .destinations({ limit: 9 })
      .then(setDests)
      .catch(() => setDests([]))
      .finally(() => setLoading(false))
  }, [])

  const search = () => {
    const params = new URLSearchParams()
    if (query) params.set('q', query)
    if (dep) params.set('departement', dep)
    const qs = params.toString()
    navigate(`/destinations${qs ? `?${qs}` : ''}`)
  }

  return (
    <div>
      {/* HERO */}
      <section className="relative overflow-hidden border-b border-line">
        <img
          src={HERO_IMAGE}
          alt="Train dans les Pays de la Loire"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/55 via-black/55 to-black/75" />

        <div className="relative z-10 px-6 py-24 text-center">
          <div className="mx-auto max-w-2xl">
            <div className="mb-6 text-[0.68rem] font-bold uppercase tracking-[0.14em] text-white/75">
              Pays de la Loire - Tourisme en train
            </div>
            <h1 className="mb-6 text-5xl font-black leading-[1.05] tracking-tighter text-white drop-shadow-lg md:text-6xl">
              Ou voulez-vous
              <br />
              aller <span className="text-violet-light">en train ?</span>
            </h1>
            <p className="mb-9 text-base leading-relaxed text-white/85 drop-shadow">
              Decouvrez les Pays de la Loire a travers ses gares, ses paysages et ses lieux uniques.
            </p>

            {/* Barre de recherche + filtres */}
            <div className="mx-auto flex max-w-2xl flex-col gap-2 rounded-2xl border border-white/10 bg-white p-2 shadow-[0_8px_32px_rgba(0,0,0,0.25)] sm:flex-row sm:items-center">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && search()}
                placeholder="Une ville : Nantes, Le Mans, Saumur..."
                className="h-12 flex-1 rounded-xl bg-transparent px-4 text-sm text-ink outline-none placeholder:text-muted"
              />
              <div className="hidden h-7 w-px bg-black/10 sm:block" />
              <select
                value={dep}
                onChange={(e) => setDep(e.target.value)}
                className="h-12 rounded-xl bg-transparent px-3 text-sm text-ink outline-none"
              >
                <option value="">Tous les departements</option>
                {deps.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              <button
                onClick={search}
                className="h-12 rounded-xl bg-violet px-7 text-sm font-semibold text-white transition hover:bg-violet-dark"
              >
                Rechercher
              </button>
            </div>

            {/* Chiffres cles, en discret */}
            {stats && (
              <p className="mt-6 text-sm font-medium text-white/75">
                {stats.nb_gares} gares &nbsp;·&nbsp; {stats.nb_lieux?.toLocaleString('fr-FR')} lieux
                &nbsp;·&nbsp; -{stats.co2_vs_voiture_pct}% CO2 vs voiture
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Profils */}
      <section className="bg-neutral-100 px-6 py-14">
        <div className="mx-auto max-w-page">
          <h2 className="text-3xl font-black tracking-tighter text-ink">
            Quel type de voyageur etes-vous ?
          </h2>
          <p className="mb-8 mt-1 text-sm text-muted">
            Votre profil - des recommandations sur mesure
          </p>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
            {PROFILS.map((p) => (
              <ProfilCard key={p.nom} nom={p.nom} desc={p.desc} />
            ))}
          </div>
        </div>
      </section>

      {/* Filtres rapides par departement */}
      <CategoryChips
        items={[
          { label: 'Toutes les destinations', value: null },
          ...deps.map((d) => ({ label: d, value: d })),
        ]}
        active={null}
        onSelect={(v) =>
          navigate(`/destinations${v ? `?departement=${encodeURIComponent(v)}` : ''}`)
        }
      />

      {/* Destinations */}
      <section className="mx-auto max-w-page px-6 py-14">
        <div className="mb-9 flex items-end justify-between">
          <div>
            <h2 className="text-3xl font-black tracking-tighter text-ink">
              Destinations incontournables
            </h2>
            <p className="mt-1 text-sm text-muted">
              Selectionnees pour vous - attractivite + accessibilite train
            </p>
          </div>
          <button
            onClick={() => navigate('/destinations')}
            className="whitespace-nowrap text-sm font-bold text-violet hover:underline"
          >
            Voir tout &rarr;
          </button>
        </div>

        {loading ? (
          <SkeletonGrid count={9} />
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {dests.map((d) => (
              <DestinationCard key={d.nom_gare} dest={d} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
