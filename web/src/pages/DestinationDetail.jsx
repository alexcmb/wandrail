import { useEffect, useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  CircleMarker,
  Polyline,
} from 'react-leaflet'
import L from 'leaflet'
import { api } from '../lib/api'
import { destImage, poiImage } from '../lib/images'

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
const WALK_MIN_PER_KM = 12 // marche a ~5 km/h

// Distance a vol d'oiseau (km) entre deux points [lat, lon].
function haversineKm(a, b) {
  if (!a || !b) return 0
  const R = 6371
  const toRad = (x) => (x * Math.PI) / 180
  const dLat = toRad(b[0] - a[0])
  const dLon = toRad(b[1] - a[1])
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(a[0])) * Math.cos(toRad(b[0])) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

const storageKey = (nom) => `wandrail:itin:${nom}`

export default function DestinationDetail() {
  const { nom } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(false)
  const [cat, setCat] = useState('Tout')
  const [selected, setSelected] = useState([]) // noms de lieux selectionnes

  // Chargement de la destination + restauration de l'itineraire sauvegarde.
  useEffect(() => {
    setData(null)
    setError(false)
    setCat('Tout')
    try {
      setSelected(JSON.parse(localStorage.getItem(storageKey(nom))) || [])
    } catch {
      setSelected([])
    }
    api.destination(nom).then(setData).catch(() => setError(true))
  }, [nom])

  // Met a jour la selection ET la persiste (par destination).
  const updateSelected = (updater) =>
    setSelected((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      try {
        localStorage.setItem(storageKey(nom), JSON.stringify(next))
      } catch {
        /* quota / mode prive : on ignore */
      }
      return next
    })

  const toggle = (name) =>
    updateSelected((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name],
    )

  const pois = data?.pois || []

  const cats = useMemo(
    () => ['Tout', ...new Set(pois.map((p) => p.categorie).filter(Boolean))],
    [pois],
  )

  const visible = useMemo(
    () => pois.filter((p) => cat === 'Tout' || p.categorie === cat).slice(0, 60),
    [pois, cat],
  )

  // Itineraire = lieux selectionnes, ordonnes par distance a la gare.
  const itinerary = useMemo(
    () =>
      pois
        .filter((p) => selected.includes(p.nom))
        .sort((a, b) => (a.distance_gare_km || 0) - (b.distance_gare_km || 0)),
    [selected, pois],
  )

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

  const d = data.destination
  const ville = cap(d.commune || d.nom_gare)
  const center = [d.latitude, d.longitude]
  const sncfUrl = `https://www.sncf-connect.com/app/home/search?destination=${encodeURIComponent(ville)}`

  // Calcul des troncons reels (gare -> etape 1 -> etape 2 -> ...).
  const legs = itinerary.map((p, idx) => {
    const from = idx === 0 ? center : [itinerary[idx - 1].latitude, itinerary[idx - 1].longitude]
    const to = [p.latitude, p.longitude]
    const km = p.latitude && p.longitude ? haversineKm(from, to) : 0
    return { km, min: Math.round(km * WALK_MIN_PER_KM) }
  })
  const totalKm = legs.reduce((s, l) => s + l.km, 0)
  const totalWalk = Math.round(totalKm * WALK_MIN_PER_KM)

  const itinPoints = itinerary
    .filter((p) => p.latitude && p.longitude)
    .map((p) => [p.latitude, p.longitude])
  const linePositions = [center, ...itinPoints]

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
              <MapContainer center={center} zoom={13} className="h-full w-full" scrollWheelZoom={true}>
                <TileLayer
                  attribution='&copy; OpenStreetMap'
                  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />
                <Circle center={center} radius={2000} pathOptions={{ color: '#7c3aed', fillOpacity: 0.05 }} />
                <Marker position={center} icon={icon}>
                  <Popup>Gare de {ville}</Popup>
                </Marker>

                {/* Trace de l'itineraire selectionne */}
                {itinPoints.length > 0 && (
                  <Polyline positions={linePositions} pathOptions={{ color: '#7c3aed', weight: 3, dashArray: '6 6' }} />
                )}
                {itinPoints.map((pos, i) => (
                  <CircleMarker
                    key={`it-${i}`}
                    center={pos}
                    radius={9}
                    pathOptions={{ color: '#fff', weight: 2, fillColor: '#7c3aed', fillOpacity: 1 }}
                  >
                    <Popup>
                      Etape {i + 1} : {itinerary[i].nom}
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            </div>
          </div>
        )}

        {/* Lieux + itineraire */}
        <div className="mt-10 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Colonne lieux */}
          <div className="lg:col-span-2">
            <h2 className="mb-1 text-2xl font-black tracking-tighter text-ink">Lieux a proximite de la gare</h2>
            <p className="mb-4 text-sm text-muted">Cliquez sur un lieu pour l'ajouter a votre itineraire.</p>

            {/* Filtres par categorie */}
            <div className="no-scrollbar mb-5 flex gap-2 overflow-x-auto pb-1">
              {cats.map((c) => (
                <button
                  key={c}
                  onClick={() => setCat(c)}
                  className={`flex-shrink-0 whitespace-nowrap rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors ${
                    cat === c
                      ? 'border-violet bg-violet text-white'
                      : 'border-black/15 bg-white text-muted hover:border-violet hover:text-violet'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {visible.map((p, i) => {
                const isSel = selected.includes(p.nom)
                return (
                  <button
                    key={`${p.nom}-${i}`}
                    onClick={() => toggle(p.nom)}
                    className={`group overflow-hidden rounded-xl border bg-white text-left shadow-card transition-all ${
                      isSel ? 'border-violet ring-2 ring-violet/20' : 'border-line hover:border-violet/40'
                    }`}
                  >
                    <div className="relative h-32 overflow-hidden bg-neutral-100">
                      <img
                        src={poiImage(p.categorie, p.nom)}
                        alt={cap(p.nom)}
                        loading="lazy"
                        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                      <span className="absolute left-2 top-2 rounded-full bg-black/55 px-2 py-0.5 text-[0.65rem] font-semibold text-white backdrop-blur">
                        {p.categorie}
                      </span>
                      <span
                        className={`absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full text-sm font-bold shadow ${
                          isSel ? 'bg-violet text-white' : 'bg-white/90 text-ink'
                        }`}
                      >
                        {isSel ? '✓' : '+'}
                      </span>
                    </div>
                    <div className="p-3">
                      <div className="truncate font-bold text-ink">{cap(p.nom)}</div>
                      <div className="mt-0.5 text-xs text-muted">
                        {p.distance_gare_km != null ? `${Number(p.distance_gare_km).toFixed(1)} km` : ''}
                        {p.temps_marche_min != null ? ` - ${Math.round(p.temps_marche_min)} min a pied` : ''}
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
            {pois.length === 0 && <p className="text-sm text-muted">Aucun lieu enregistre a proximite.</p>}
          </div>

          {/* Colonne itineraire (sticky) */}
          <aside className="h-fit lg:sticky lg:top-20">
            <div className="rounded-2xl border border-line bg-white p-5 shadow-card">
              <h3 className="text-lg font-black tracking-tight text-ink">Mon itineraire</h3>

              {itinerary.length === 0 ? (
                <p className="mt-3 text-sm leading-relaxed text-muted">
                  Selectionnez des activites dans la liste pour composer votre journee. Le parcours
                  s'affichera sur la carte, ordonne par distance a la gare. Il est sauvegarde
                  automatiquement.
                </p>
              ) : (
                <>
                  <div className="mt-2 mb-4 text-xs font-semibold text-muted">
                    {itinerary.length} etape{itinerary.length > 1 ? 's' : ''}
                    {totalKm > 0 ? ` - ${totalKm.toFixed(1)} km - ~${totalWalk} min de marche` : ''}
                  </div>
                  <ol className="space-y-0">
                    <li className="flex items-center gap-3 rounded-lg bg-neutral-50 px-3 py-2">
                      <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-ink text-xs font-bold text-white">
                        G
                      </span>
                      <span className="text-sm font-semibold text-ink">Gare de {ville}</span>
                    </li>
                    {itinerary.map((p, idx) => (
                      <div key={`${p.nom}-${idx}`}>
                        {/* Troncon depuis l'etape precedente */}
                        <div className="ml-3 flex items-center gap-2 py-1 pl-3 text-[0.7rem] text-muted">
                          <span className="h-4 w-px bg-violet/40" />
                          {legs[idx].km > 0
                            ? `${legs[idx].km.toFixed(1)} km - ~${legs[idx].min} min a pied`
                            : 'a proximite'}
                        </div>
                        <li className="flex items-start gap-3 rounded-lg border border-line px-3 py-2">
                          <span className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-violet text-xs font-bold text-white">
                            {idx + 1}
                          </span>
                          <div className="min-w-0 flex-1">
                            <div className="truncate text-sm font-semibold text-ink">{cap(p.nom)}</div>
                            <div className="text-xs text-muted">{p.categorie}</div>
                          </div>
                          <button
                            onClick={() => toggle(p.nom)}
                            className="text-muted hover:text-violet"
                            aria-label="Retirer"
                          >
                            {'×'}
                          </button>
                        </li>
                      </div>
                    ))}
                  </ol>
                  <button
                    onClick={() => updateSelected([])}
                    className="mt-4 w-full rounded-lg border border-line py-2 text-sm font-semibold text-muted transition hover:border-violet hover:text-violet"
                  >
                    Vider l'itineraire
                  </button>
                </>
              )}
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
