import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import Logo from './Logo'
import LoginModal from './LoginModal'

const links = [
  { to: '/', label: 'Accueil', end: true },
  { to: '/destinations', label: 'Destinations' },
]

export default function Navbar() {
  const [loginOpen, setLoginOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-white/95 backdrop-blur">
      <div className="mx-auto grid h-16 max-w-page grid-cols-[1fr_auto_1fr] items-center px-6">
        {/* Gauche : logo */}
        <Link to="/" className="justify-self-start">
          <Logo textClass="text-2xl" />
        </Link>

        {/* Milieu : navigation */}
        <nav className="hidden items-center gap-1 justify-self-center md:flex">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                `flex h-16 items-center border-b-[3px] px-4 text-sm font-semibold transition-colors ${
                  isActive
                    ? 'border-violet text-violet'
                    : 'border-transparent text-muted hover:text-violet'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        {/* Droite : connexion */}
        <div className="justify-self-end">
          <button
            onClick={() => setLoginOpen(true)}
            className="inline-flex items-center gap-2 rounded-full bg-violet px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-violet/30 ring-1 ring-violet/20 transition hover:bg-violet-dark hover:shadow-violet/50"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.2">
              <circle cx="12" cy="8" r="4" />
              <path d="M4 21c0-4 4-6 8-6s8 2 8 6" strokeLinecap="round" />
            </svg>
            Se connecter
          </button>
        </div>
      </div>

      <LoginModal open={loginOpen} onClose={() => setLoginOpen(false)} />
    </header>
  )
}
