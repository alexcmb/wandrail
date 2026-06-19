import { Link } from 'react-router-dom'
import Logo from './Logo'

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-line bg-neutral-50 px-6 py-14 text-center">
      <div className="flex justify-center">
        <Logo textClass="text-3xl" />
      </div>
      <p className="mx-auto mt-4 max-w-md text-sm italic text-muted">
        Laissez une escale devenir une aventure.
      </p>
      <div className="mt-6 flex justify-center gap-7 text-sm font-medium text-muted">
        <Link to="/" className="hover:text-violet">
          Accueil
        </Link>
        <Link to="/destinations" className="hover:text-violet">
          Destinations
        </Link>
      </div>
      <p className="mt-8 text-xs text-muted/70">© 2026 Wandrail - Tous droits reserves</p>
    </footer>
  )
}
