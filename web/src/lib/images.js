// Mapping image par destination (porte depuis l'app Streamlit).
// On utilise picsum.photos avec des IDs choisis pour ressembler aux villes.
// Cle = mot present dans le nom de la commune/gare (en minuscules).

const DEST_IMG = {
  saumur: 40,
  'le mans': 175,
  angers: 192,
  nantes: 130,
  'saint-nazaire': 116,
  'st-nazaire': 116,
  'la baule': 169,
  'le pouliguen': 76,
  laval: 181,
  'le croisic': 74,
  cholet: 583,
  pornic: 76,
  'les sables': 169,
  'la roche-sur-yon': 103,
  clisson: 40,
  'fontenay-le-comte': 826,
}

// IDs de secours de bonne qualite (paysages / villes).
const FALLBACK_IDS = [
  175, 100, 103, 192, 181, 130, 116, 169, 76, 74, 583, 248, 379, 431, 592, 826,
]

function hashString(str) {
  let sum = 0
  for (let i = 0; i < str.length; i += 1) sum += str.charCodeAt(i)
  return sum
}

export function destImage(nom, w = 800, h = 500) {
  const key = String(nom || '').toLowerCase()
  let id = null
  for (const [k, v] of Object.entries(DEST_IMG)) {
    if (key.includes(k)) {
      id = v
      break
    }
  }
  if (id == null) {
    id = FALLBACK_IDS[hashString(key) % FALLBACK_IDS.length]
  }
  return `https://picsum.photos/id/${id}/${w}/${h}`
}
