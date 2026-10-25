function Group({ title, rows }) {
  if (rows.length === 0) return null
  return (
    <div className="change-group">
      <h3>{title}</h3>
      <ul>
        {rows.map((text, i) => (
          <li key={text + i}>{text}</li>
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
      <h2>What changed since last time?</h2>
      {nothing && <p>Good news: everything is right where you left it.</p>}
      <Group title="What’s changed" rows={moved} />
      <Group title="What’s missing" rows={missing} />
      <Group title="What’s new" rows={added} />
    </section>
  )
}
