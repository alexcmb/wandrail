import { useNavigate } from 'react-router-dom'

export default function ProfilCard({ nom, desc, profilFilter }) {
  const navigate = useNavigate()
  return (
    <button
      type="button"
      onClick={() =>
        navigate(`/destinations${profilFilter ? `?profil=${encodeURIComponent(profilFilter)}` : ''}`)
      }
      className="group rounded-2xl border border-line bg-white p-7 text-left shadow-card transition-all duration-200 hover:-translate-y-1 hover:border-violet/60 hover:shadow-cardHover"
    >
      <div className="mb-2.5 text-base font-extrabold tracking-tight text-ink">{nom}</div>
      <p className="text-sm leading-relaxed text-muted">{desc}</p>
    </button>
  )
}
