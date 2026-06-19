import { useEffect, useState } from 'react'

// Recupere une vraie photo de la ville depuis Wikipedia (resume REST).
// Repli sur l'image fournie (picsum) si aucune photo n'est trouvee.
// Cache module pour ne jamais refaire deux fois la meme requete.

const cache = new Map() // commune (minuscule) -> url | null | Promise

const cap = (s) => String(s || '').replace(/\b\w/g, (c) => c.toUpperCase())

function fetchPlaceImage(commune) {
  const key = String(commune || '').toLowerCase().trim()
  if (!key) return Promise.resolve(null)
  if (cache.has(key)) return Promise.resolve(cache.get(key))

  const p = fetch(`https://fr.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(cap(key))}`)
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => {
      // On prefere l'image originale (toujours servie, bonne qualite) tant
      // qu'elle reste raisonnable ; sinon la vignette. Les tailles
      // intermediaires generees a la volee par Wikimedia sont peu fiables.
      const orig = d && d.originalimage
      const thumb = d && d.thumbnail
      let url = null
      if (orig && orig.source && (orig.width || 0) <= 2600) url = orig.source
      else if (thumb && thumb.source) url = thumb.source
      else if (orig && orig.source) url = orig.source
      cache.set(key, url)
      return url
    })
    .catch(() => {
      cache.set(key, null)
      return null
    })

  cache.set(key, p) // memorise la promesse pour dedupliquer les appels simultanes
  return p
}

export function usePlaceImage(commune, fallback) {
  const [url, setUrl] = useState(fallback)
  useEffect(() => {
    let cancelled = false
    setUrl(fallback)
    fetchPlaceImage(commune).then((u) => {
      if (!cancelled && u) setUrl(u)
    })
    return () => {
      cancelled = true
    }
  }, [commune, fallback])
  return url
}
