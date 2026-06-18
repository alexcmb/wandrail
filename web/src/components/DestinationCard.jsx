import { Link } from 'react-router-dom'
import { destImage } from '../lib/images'

const cap = (s) => String(s || '').replace(/\b\w/g, (c) => c.toUpperCase())

export default function DestinationCard({ dest }) {
  const ville = cap(dest.commune || dest.nom_gare)
  const score = dest.score_attractivite != null ? Number(dest.score_attractivite) : null

  return (
    <Link
      to={`/destinations/${encodeURIComponent(dest.nom_gare)}`}
      className="group block overflow-hidden rounded-2xl border border-line bg-white shadow-card transition-all duration-300 hover:-translate-y-1.5 hover:border-transparent hover:shadow-cardHover"
    >
      <div className="relative h-60 overflow-hidden bg-neutral-100">
        <img
          src={destImage(dest.commune || dest.nom_gare)}
          alt={ville}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-[600ms] ease-out group-hover:scale-[1.06]"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-black/5 to-transparent" />

        {score != null && (
          <span className="absolute right-3 top-3 rounded-full bg-white/95 px-2.5 py-1 text-xs font-bold text-ink shadow-sm backdrop-blur">
            {score.toFixed(1)}
          </span>
        )}

        <div className="absolute bottom-4 left-5 right-5">
          <div className="text-[1.1rem] font-extrabold tracking-tight text-white drop-shadow">
            {ville}
          </div>
          <div className="text-xs font-medium text-white/80">{cap(dest.departement)}</div>
        </div>
      </div>

      <div className="flex items-center justify-between px-4 py-3.5">
        <span className="text-sm font-medium text-muted">
          {dest.nb_poi_5km ? `${dest.nb_poi_5km.toLocaleString('fr-FR')} activites` : 'A decouvrir'}
        </span>
        <span className="text-sm font-bold text-violet opacity-0 transition-opacity duration-200 group-hover:opacity-100">
          Explorer &rarr;
        </span>
      </div>
    </Link>
  )
}
