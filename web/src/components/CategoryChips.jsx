export default function CategoryChips({ items, active, onSelect }) {
  return (
    <div className="no-scrollbar flex gap-2.5 overflow-x-auto border-b border-line px-6 py-5">
      {items.map((item) => {
        const isActive = active === item.value
        return (
          <button
            key={item.label}
            type="button"
            onClick={() => onSelect(item.value)}
            className={`flex-shrink-0 whitespace-nowrap rounded-3xl border px-6 py-2 text-sm font-semibold transition-colors ${
              isActive
                ? 'border-violet bg-violet text-white'
                : 'border-black/20 bg-white text-muted hover:border-violet hover:text-violet'
            }`}
          >
            {item.label}
          </button>
        )
      })}
    </div>
  )
}
