export default function Footer() {
  return (
    <footer className="mt-16 bg-[#111111] px-6 py-12 text-center text-white/40">
      <div className="mb-3 text-lg font-extrabold tracking-tight text-white/70">
        Wand<span className="text-violet">rail</span>
      </div>
      <p className="mx-auto max-w-xl text-sm leading-relaxed">
        Projet M1 Big Data &amp; IA - Sup de Vinci - Partenariat SNCF Open Data University Saison 3
      </p>
      <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-xs">
        <span>SNCF Open Data</span>
        <span className="text-white/15">|</span>
        <span>Donnees ADEME CO2</span>
        <span className="text-white/15">|</span>
        <span>Picsum Photos</span>
      </div>
      <p className="mt-6 text-xs text-white/25">
        RNCP40167 - Sup de Vinci - 2026 Thilissa Amara
      </p>
    </footer>
  )
}
