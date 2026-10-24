const TABS = [
  { id: 'scan', label: 'Scan' },
  { id: 'search', label: 'Search' },
  { id: 'history', label: 'History' },
]

export default function BottomNav({ tab, setTab }) {
  return (
    <nav className="bottom-nav" aria-label="Main">
      <div className="bottom-nav-inner">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            aria-current={tab === id ? 'page' : undefined}
          >
            {label}
          </button>
        ))}
      </div>
    </nav>
  )
}
