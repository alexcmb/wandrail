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
            className="rounded-full bg-violet px-5 py-2 text-sm font-semibold text-white transition hover:bg-violet-dark"
          >
            Se connecter
          </button>
        </div>
      </div>

      <LoginModal open={loginOpen} onClose={() => setLoginOpen(false)} />
    </header>
  )
}
