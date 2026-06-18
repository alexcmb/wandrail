import { Link } from 'react-router-dom'
import { destImage } from '../lib/images'

export default function DestinationCard({ dest }) {
  const ville = (dest.commune || dest.nom_gare || '').replace(/\b\w/g, (c) => c.toUpperCase())
  return (
    <Link
      to={`/destinations/${encodeURIComponent(dest.nom_gare)}`}
      className="group block overflow-hidden rounded-2xl border border-line bg-white shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-transparent hover:shadow-cardHover"
    >
      <div className="relative h-60 overflow-hidden bg-neutral-100">
        <img
          src={destImage(dest.commune || dest.nom_gare)}
          alt={ville}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
        <span className="absolute bottom-4 left-5 right-5 text-[1.08rem] font-extrabold tracking-tight text-white drop-shadow">
          {ville}
        </span>
      </div>
      <div className="px-4 pb-4 pt-4">
        <div className="text-sm font-medium text-muted">
          {(dest.departement || '').replace(/\b\w/g, (c) => c.toUpperCase())}
          {dest.nb_poi_5km ? ` - ${dest.nb_poi_5km} activites` : ''}
        </div>
      </div>
    </Link>
  )
}
