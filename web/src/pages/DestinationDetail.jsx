import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import L from 'leaflet'
import { api } from '../lib/api'
import { destImage } from '../lib/images'

// Corrige les icones Leaflet (chemins casses par le bundler Vite).
const icon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const cap = (s) => String(s || '').replace(/\b\w/g, (c) => c.toUpperCase())

export default function DestinationDetail() {
  const { nom } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    setData(null)
    setError(false)
    api.destination(nom).then(setData).catch(() => setError(true))
  }, [nom])

  if (error) {
    return (
      <div className="mx-auto max-w-page px-6 py-24 text-center text-muted">
        Destination introuvable.{' '}
        <Link to="/destinations" className="font-semibold text-violet">
          Retour
        </Link>
      </div>
    )
  }

  if (!data) {
    return <div className="mx-auto max-w-page px-6 py-24 text-center text-muted">Chargement...</div>
  }

  const { destination: d, pois } = data
  const ville = cap(d.commune || d.nom_gare)
  const center = [d.latitude, d.longitude]
  const sncfUrl = `https://www.sncf-connect.com/app/home/search?destination=${encodeURIComponent(ville)}`

  return (
    <div>
      {/* Hero image */}
      <div className="relative h-80 overflow-hidden bg-neutral-900">
        <img src={destImage(d.commune || d.nom_gare, 1600, 700)} alt={ville} className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 mx-auto max-w-page px-6 pb-7">
          <Link to="/destinations" className="mb-3 inline-block text-sm font-semibold text-white/70 hover:text-white">
            &larr; Toutes les destinations
          </Link>
          <h1 className="text-4xl font-black tracking-tighter text-white drop-shadow md:text-5xl">{ville}</h1>
          <p className="mt-1 text-sm text-white/70">
            {cap(d.departement)}
            {d.profil_touristique ? ` - Profil ${d.profil_touristique}` : ''}
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-page px-6 py-10">
        {/* Stats destination */}
        <div className="mb-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { v: d.score_attractivite != null ? Number(d.score_attractivite).toFixed(1) : '-', l: 'Score attractivite' },
            { v: d.nb_poi_5km ?? '-', l: 'Lieux a 5 km' },
            { v: d.nb_categories ?? '-', l: 'Categories' },
            { v: pois.length, l: 'Lieux affiches' },
          ].map((s) => (
            <div key={s.l} className="rounded-2xl border border-line bg-white p-5 text-center shadow-card">
              <div className="text-2xl font-extrabold tracking-tighter text-violet">{s.v}</div>
              <div className="mt-1 text-xs font-medium text-muted">{s.l}</div>
            </div>
          ))}
        </div>

        <a
          href={sncfUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg bg-[#e2001a] px-5 py-2.5 text-sm font-bold text-white transition hover:opacity-90"
        >
          Reserver un billet sur SNCF Connect
        </a>

        {/* Carte */}
        {d.latitude && d.longitude && (
          <div className="mt-10">
            <h2 className="mb-4 text-2xl font-black tracking-tighter text-ink">Carte des environs</h2>
            <div className="h-[420px] overflow-hidden rounded-2xl border border-line">
              <MapContainer center={center} zoom={13} className="h-full w-full" scrollWheelZoom={false}>
                <TileLayer
                  attribution='&copy; OpenStreetMap'
                  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />
                <Circle center={center} radius={2000} pathOptions={{ color: '#7c3aed', fillOpacity: 0.05 }} />
                <Marker position={center} icon={icon}>
                  <Popup>Gare de {ville}</Popup>
                </Marker>
                {pois.slice(0, 120).map((p, i) =>
                  p.latitude && p.longitude ? (
                    <Marker key={i} position={[p.latitude, p.longitude]} icon={icon}>
                      <Popup>
                        <strong>{p.nom}</strong>
                        <br />
                        {p.categorie}
                        {p.distance_gare_km != null ? ` - ${Number(p.distance_gare_km).toFixed(1)} km` : ''}
                      </Popup>
                    </Marker>
                  ) : null,
                )}
              </MapContainer>
            </div>
          </div>
        )}

        {/* Liste des POI */}
        <div className="mt-10">
          <h2 className="mb-4 text-2xl font-black tracking-tighter text-ink">
            Lieux a proximite de la gare
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {pois.slice(0, 60).map((p, i) => (
              <div key={i} className="rounded-xl border border-line bg-white p-4 shadow-card">
                <div className="font-bold text-ink">{cap(p.nom)}</div>
                <div className="mt-1 text-xs text-muted">
                  {p.categorie}
                  {p.distance_gare_km != null ? ` - ${Number(p.distance_gare_km).toFixed(1)} km` : ''}
                  {p.temps_marche_min != null ? ` - ${Math.round(p.temps_marche_min)} min a pied` : ''}
                </div>
              </div>
            ))}
          </div>
          {pois.length === 0 && (
            <p className="text-sm text-muted">Aucun lieu enregistre a proximite.</p>
          )}
        </div>
      </div>
    </div>
  )
}
