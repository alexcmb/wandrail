import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

// Remet la page en haut a chaque changement de route (comportement attendu
// d'un vrai site, que React Router ne fait pas par defaut).
export default function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}
