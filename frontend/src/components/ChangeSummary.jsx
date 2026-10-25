function Group({ title, rows }) {
  if (rows.length === 0) return null
  return (
    <div className="change-group">
      <h3>{title}</h3>
      <ul>
        {rows.map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
    </div>
  )
}

export default function ChangeSummary({ changes }) {
  const moved = changes.moved.map((m) => `${m.label} moved from ${m.from_position} to ${m.to_position}`)
  const missing = changes.missing.map((m) => `${m.label} was last seen ${m.last_position}`)
  const added = changes.new.map((n) => `${n.label} is new, ${n.position}`)
  const nothing = moved.length + missing.length + added.length === 0

  return (
    <section className="card">
      <h2>What changed since last time</h2>
      {nothing && <p>Nothing has moved since the previous scan.</p>}
      <Group title="Moved" rows={moved} />
      <Group title="Missing" rows={missing} />
      <Group title="New" rows={added} />
    </section>
  )
}
