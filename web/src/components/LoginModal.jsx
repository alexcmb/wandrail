import { useState } from 'react'
import Logo from './Logo'

// Panneau de connexion latéral (interface uniquement pour ce POC : l'authentification
// réelle sera branchée sur l'API plus tard).
export default function LoginModal({ open, onClose }) {
  const [mode, setMode] = useState('login') // login | signup
  const [msg, setMsg] = useState('')

  const submit = (e) => {
    e.preventDefault()
    setMsg('La connexion sera bientôt disponible (interface de démonstration).')
  }

  return (
    <div
      className={`fixed inset-0 z-[100] transition-all duration-300 ${
        open ? 'visible' : 'invisible'
      }`}
    >
      {/* Arrière-plan sombre et flouté */}
      <div
        className={`fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-300 ${
          open ? 'opacity-100' : 'opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Panneau latéral (Drawer) */}
      <div
        style={{ backgroundColor: '#ffffff' }}
        className={`fixed inset-y-0 right-0 z-[101] flex h-full w-full max-w-sm flex-col justify-between bg-white p-7 shadow-2xl transition-transform duration-300 ease-in-out transform ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div>
          {/* En-tête */}
          <div className="flex items-center justify-between">
            <Logo textClass="text-xl" />
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full text-2xl leading-none text-muted transition hover:bg-neutral-100 hover:text-ink"
              aria-label="Fermer"
            >
              {'×'}
            </button>
          </div>

          {/* Titre */}
          <h2 className="mt-8 text-2xl font-black tracking-tight text-ink">
            {mode === 'login' ? 'Connexion' : 'Créer un compte'}
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Retrouvez vos itinéraires et vos destinations favorites.
          </p>

          {/* Formulaire */}
          <form className="mt-6 space-y-4" onSubmit={submit}>
            {mode === 'signup' && (
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-muted">
                  Nom d'utilisateur
                </label>
                <input
                  type="text"
                  placeholder="nom d'utilisateur"
                  required
                  className="mt-1.5 h-11 w-full rounded-xl border-[1.5px] border-black/15 bg-neutral-50 px-4 text-sm outline-none transition focus:border-violet focus:bg-white"
                />
              </div>
            )}
            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-muted">
                Adresse e-mail
              </label>
              <input
                type="email"
                placeholder="nom@exemple.com"
                required
                className="mt-1.5 h-11 w-full rounded-xl border-[1.5px] border-black/15 bg-neutral-50 px-4 text-sm outline-none transition focus:border-violet focus:bg-white"
              />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-muted">
                  Mot de passe
                </label>
                {mode === 'login' && (
                  <button type="button" className="text-xs font-semibold text-violet hover:underline">
                    Oublié ?
                  </button>
                )}
              </div>
              <input
                type="password"
                placeholder="••••••••"
                required
                className="mt-1.5 h-11 w-full rounded-xl border-[1.5px] border-black/15 bg-neutral-50 px-4 text-sm outline-none transition focus:border-violet focus:bg-white"
              />
            </div>
            <button
              type="submit"
              className="mt-2 h-11 w-full rounded-xl bg-violet text-sm font-semibold text-white shadow-lg shadow-violet/20 transition hover:bg-violet-dark hover:shadow-violet/30"
            >
              {mode === 'login' ? 'Se connecter' : "S'inscrire"}
            </button>
          </form>

          {msg && (
            <div className="mt-4 rounded-xl bg-violet-light/10 p-3.5 text-center text-xs font-medium text-violet-dark">
              {msg}
            </div>
          )}
        </div>

        {/* Pied du Drawer */}
        <div className="border-t border-line pt-5 text-center text-xs text-muted">
          {mode === 'login' ? 'Pas encore de compte ? ' : 'Déjà un compte ? '}
          <button
            onClick={() => {
              setMode(mode === 'login' ? 'signup' : 'login')
              setMsg('')
            }}
            className="font-bold text-violet hover:underline"
          >
            {mode === 'login' ? 'Créer un compte' : 'Se connecter'}
          </button>
        </div>
      </div>
    </div>
  )
}
