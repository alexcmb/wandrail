import { Link, NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Accueil', end: true },
  { to: '/destinations', label: 'Destinations' },
]

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-page items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2 text-lg font-extrabold tracking-tight">
          <span className="h-2 w-2 rounded-full bg-gradient-to-br from-violet to-orange-500" />
          Wand<span className="text-violet">rail</span>
        </Link>

        <nav className="flex items-center gap-1">
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
      </div>
    </header>
  )
}
