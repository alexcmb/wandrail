import { useState } from 'react'
import Logo from './Logo'

// Fenetre de connexion (interface uniquement pour ce POC : l'authentification
// reelle sera branchee sur l'API plus tard).
export default function LoginModal({ open, onClose }) {
  const [mode, setMode] = useState('login') // login | signup
  const [msg, setMsg] = useState('')

  if (!open) return null

  const submit = (e) => {
    e.preventDefault()
    setMsg('La connexion sera bientot disponible (interface de demonstration).')
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm rounded-2xl bg-white p-7 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <Logo textClass="text-xl" />
          <button onClick={onClose} className="text-2xl leading-none text-muted hover:text-ink" aria-label="Fermer">
            {'×'}
          </button>
        </div>

        <h2 className="mt-5 text-xl font-black tracking-tight text-ink">
          {mode === 'login' ? 'Connexion' : 'Creer un compte'}
        </h2>
        <p className="mt-1 text-sm text-muted">
          Retrouvez vos itineraires et vos destinations favorites.
        </p>

        <form className="mt-5 space-y-3" onSubmit={submit}>
          {mode === 'signup' && (
            <input
              type="text"
              placeholder="Nom d'utilisateur"
              className="h-11 w-full rounded-xl border-[1.5px] border-black/15 bg-neutral-50 px-4 text-sm outline-none focus:border-violet"
            />
          )}
          <input
            type="email"
            placeholder="Adresse e-mail"
            required
            className="h-11 w-full rounded-xl border-[1.5px] border-black/15 bg-neutral-50 px-4 text-sm outline-none focus:border-violet"
          />
          <input
            type="password"
            placeholder="Mot de passe"
            required
            className="h-11 w-full rounded-xl border-[1.5px] border-black/15 bg-neutral-50 px-4 text-sm outline-none focus:border-violet"
          />
          <button
            type="submit"
            className="h-11 w-full rounded-xl bg-violet text-sm font-semibold text-white transition hover:bg-violet-dark"
          >
            {mode === 'login' ? 'Se connecter' : "S'inscrire"}
          </button>
        </form>

        {msg && <p className="mt-3 text-center text-xs text-muted">{msg}</p>}

        <p className="mt-5 text-center text-xs text-muted">
          {mode === 'login' ? 'Pas encore de compte ? ' : 'Deja un compte ? '}
          <button
            onClick={() => {
              setMode(mode === 'login' ? 'signup' : 'login')
              setMsg('')
            }}
            className="font-semibold text-violet hover:underline"
          >
            {mode === 'login' ? 'Creer un compte' : 'Se connecter'}
          </button>
        </p>
      </div>
    </div>
  )
}
