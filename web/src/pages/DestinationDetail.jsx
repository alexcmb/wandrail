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
import { usePlaceImage } from '../lib/usePlaceImage'

// Gare de reference (hub regional) pour la comparaison train / voiture.
const HUB = { nom: 'Nantes', lat: 47.218371, lon: -1.541362 }
const CAR_G_PER_KM = 218 // gCO2/km (voiture, ADEME)
const TRAIN_RATIO = 0.09 // le train emet ~91% de CO2 en moins

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

// Lien Google Maps "directions" a pied : gare -> etapes intermediaires -> derniere.
function gmapsDirectionsUrl(center, points) {
  const origin = `${center[0]},${center[1]}`
  const last = points[points.length - 1]
  const destination = `${last[0]},${last[1]}`
  const params = new URLSearchParams({ api: '1', origin, destination, travelmode: 'walking' })
  const wp = points
    .slice(0, -1)
    .map(([la, lo]) => `${la},${lo}`)
    .join('|')
  if (wp) params.set('waypoints', wp)
  return `https://www.google.com/maps/dir/?${params.toString()}`
}

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

  // Vraie photo de la ville (Wikipedia) avec repli picsum.
  const communeName = data?.destination?.commune || data?.destination?.nom_gare || ''
  const heroImg = usePlaceImage(communeName, destImage(communeName, 1600, 700))

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

  // Vrai trace pieton (suivant les rues) via OSRM, recalcule a chaque
  // changement d'itineraire. Repli sur la ligne directe si indisponible.
  const [routeGeo, setRouteGeo] = useState(null)
  const [routeInfo, setRouteInfo] = useState(null)
  const routeKey = itinerary.map((p) => p.nom).join('|')

  useEffect(() => {
    if (!data || itinerary.length === 0) {
      setRouteGeo(null)
      setRouteInfo(null)
      return
    }
    const c = [data.destination.latitude, data.destination.longitude]
    const pts = itinerary
      .filter((p) => p.latitude && p.longitude)
      .map((p) => [p.latitude, p.longitude])
    if (pts.length === 0) {
      setRouteGeo(null)
      setRouteInfo(null)
      return
    }
    const coordStr = [c, ...pts].map(([la, lo]) => `${lo},${la}`).join(';')
    let cancelled = false
    fetch(`https://router.project-osrm.org/route/v1/foot/${coordStr}?overview=full&geometries=geojson`)
      .then((r) => r.json())
      .then((j) => {
        if (cancelled) return
        const route = j.code === 'Ok' && j.routes && j.routes[0]
        if (route && route.geometry?.coordinates?.length > 1) {
          // On garde la distance routiere reelle, mais on recalcule le temps a
          // pied (le serveur de demo OSRM renvoie des durees de type voiture).
          const km = route.distance / 1000
          setRouteGeo(route.geometry.coordinates.map(([lo, la]) => [la, lo]))
          setRouteInfo({
            km,
            min: Math.round(km * WALK_MIN_PER_KM),
            legs: (route.legs || []).map((l) => {
              const legKm = l.distance / 1000
              return { km: legKm, min: Math.round(legKm * WALK_MIN_PER_KM) }
            }),
          })
        } else {
          setRouteGeo(null)
          setRouteInfo(null)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRouteGeo(null)
          setRouteInfo(null)
        }
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeKey, data])

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

  // Totaux affiches : vrai trace OSRM si dispo, sinon estimation a vol d'oiseau.
  const displayKm = routeInfo ? routeInfo.km : totalKm
  const displayMin = routeInfo ? routeInfo.min : totalWalk
  const useRealLegs = routeInfo && routeInfo.legs.length === itinerary.length
  const directionsUrl = itinPoints.length > 0 ? gmapsDirectionsUrl(center, itinPoints) : null

  // Comparaison train vs voiture, aller-retour depuis le hub (Nantes).
  const distKm = haversineKm([HUB.lat, HUB.lon], center)
  const distAR = distKm * 2
  const carCo2 = (CAR_G_PER_KM * distAR) / 1000 // kg
  const trainCo2 = carCo2 * TRAIN_RATIO
  const co2Saved = carCo2 - trainCo2
  const carTimeMin = Math.round((distAR / 75) * 60) // ~75 km/h porte a porte
  const trainTimeMin = Math.round((distAR / 80) * 60) // ~80 km/h moyenne TER
  const carCost = distAR * 0.25 // EUR (carburant + usure)
  const trainCost = distAR * 0.13 // EUR (estimation billet TER)
  const fmtTime = (m) => (m >= 60 ? `${Math.floor(m / 60)}h${String(m % 60).padStart(2, '0')}` : `${m} min`)
  const showCompare = distKm >= 2

  return (
    <div>
      {/* Hero image */}
      <div className="relative h-80 overflow-hidden bg-neutral-900">
        <img src={heroImg} alt={ville} className="h-full w-full object-cover" />
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

        {/* Comparaison Train vs Voiture */}
        {showCompare && (
          <div className="mt-10">
            <h2 className="mb-1 text-2xl font-black tracking-tighter text-ink">Train ou voiture ?</h2>
            <p className="mb-4 text-sm text-muted">
              Aller-retour depuis {HUB.nom} ({Math.round(distAR)} km) - estimations indicatives.
            </p>
            <div className="overflow-hidden rounded-2xl border border-line shadow-card">
              <div className="grid grid-cols-3 border-b border-line bg-neutral-50 text-xs font-bold uppercase tracking-wide text-muted">
                <div className="p-3" />
                <div className="p-3 text-center text-violet">Train</div>
                <div className="p-3 text-center">Voiture</div>
              </div>
              {[
                {
                  label: 'CO2 emis',
                  train: `${trainCo2.toFixed(1)} kg`,
                  car: `${carCo2.toFixed(1)} kg`,
                  good: true,
                },
                { label: 'Temps estime', train: fmtTime(trainTimeMin), car: fmtTime(carTimeMin) },
                {
                  label: 'Budget estime',
                  train: `~${trainCost.toFixed(0)} EUR`,
                  car: `~${carCost.toFixed(0)} EUR`,
                },
              ].map((row) => (
                <div key={row.label} className="grid grid-cols-3 border-b border-line text-sm last:border-0">
                  <div className="p-3 font-semibold text-ink">{row.label}</div>
                  <div className={`p-3 text-center font-bold ${row.good ? 'text-green-600' : 'text-ink'}`}>
                    {row.train}
                  </div>
                  <div className="p-3 text-center text-muted">{row.car}</div>
                </div>
              ))}
              <div className="bg-violet/5 p-3 text-center text-sm font-bold text-violet">
                En train : {co2Saved.toFixed(0)} kg de CO2 economises (~91% de moins)
              </div>
            </div>
          </div>
        )}

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

                {/* Trace de l'itineraire : vrai chemin pieton OSRM, sinon ligne directe */}
                {routeGeo ? (
                  <Polyline positions={routeGeo} pathOptions={{ color: '#7c3aed', weight: 4, opacity: 0.9 }} />
                ) : itinPoints.length > 0 ? (
                  <Polyline positions={linePositions} pathOptions={{ color: '#7c3aed', weight: 3, dashArray: '6 6' }} />
                ) : null}
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
                    {displayKm > 0 ? ` - ${displayKm.toFixed(1)} km - ~${displayMin} min a pied` : ''}
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
                          {(useRealLegs ? routeInfo.legs[idx].km : legs[idx].km) > 0
                            ? `${(useRealLegs ? routeInfo.legs[idx].km : legs[idx].km).toFixed(1)} km - ~${
                                useRealLegs ? routeInfo.legs[idx].min : legs[idx].min
                              } min a pied`
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
                  {directionsUrl && (
                    <a
                      href={directionsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-violet py-2.5 text-sm font-bold text-white transition hover:bg-violet-dark"
                    >
                      Demarrer l'itineraire
                    </a>
                  )}
                  <p className="mt-1.5 text-center text-[0.68rem] text-muted">
                    Ouvre la navigation a pied dans Google Maps
                  </p>
                  <button
                    onClick={() => updateSelected([])}
                    className="mt-3 w-full rounded-lg border border-line py-2 text-sm font-semibold text-muted transition hover:border-violet hover:text-violet"
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
