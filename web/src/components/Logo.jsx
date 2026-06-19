import { useId } from 'react'

// Logo Wandrail : mot-symbole en degrade violet -> magenta + fleche stylisee.
// Reutilisable dans la navbar, le footer et la fenetre de connexion.
export default function Logo({ textClass = 'text-2xl' }) {
  const id = useId().replace(/:/g, '')
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`bg-gradient-to-r from-[#3b0a8f] via-[#7c3aed] to-[#d6006e] bg-clip-text font-display font-black tracking-tight text-transparent ${textClass}`}
      >
        Wandrail
      </span>
      <svg viewBox="0 0 28 24" className="h-[0.85em] w-auto" style={{ marginBottom: '0.12em' }}>
        <defs>
          <linearGradient id={`wg-${id}`} x1="0" y1="1" x2="1" y2="0">
            <stop offset="0%" stopColor="#5b21b6" />
            <stop offset="100%" stopColor="#d6006e" />
          </linearGradient>
        </defs>
        {/* aile inferieure (fleche) */}
        <path d="M1 19 L25 13 L13 11 Z" fill={`url(#wg-${id})`} />
        {/* aile superieure */}
        <path d="M6 9 L27 3 L15 7 Z" fill="#d6006e" />
      </svg>
    </span>
  )
}
