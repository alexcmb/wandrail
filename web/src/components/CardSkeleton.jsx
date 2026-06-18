// Placeholder anime affiche pendant le chargement des destinations.
export function CardSkeleton() {
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-card">
      <div className="h-60 animate-pulse bg-neutral-200" />
      <div className="flex items-center justify-between px-4 py-3.5">
        <div className="h-4 w-24 animate-pulse rounded bg-neutral-200" />
        <div className="h-4 w-16 animate-pulse rounded bg-neutral-100" />
      </div>
    </div>
  )
}

export function SkeletonGrid({ count = 6 }) {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  )
}
