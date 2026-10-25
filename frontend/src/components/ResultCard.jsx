import ClipPlayer from './ClipPlayer'

function friendlyTime(iso) {
  return new Date(iso).toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' })
}

export default function ResultCard({ items, pastSightings }) {
  const several = items.length > 1
  return (
    <>
      {several && <p className="lede">We found {items.length} matches.</p>}
      {items.map((item, i) => (
        <section className="card result" key={item.label + i}>
          <h2>{several ? `${item.label} (${i + 1} of ${items.length})` : item.label}</h2>
          <p className="position">{item.position}</p>
          <p>Last seen {friendlyTime(item.seen_at)}</p>
          <p>{item.description}</p>
          {item.clip_url && <ClipPlayer src={item.clip_url} startSeconds={item.clip_start_seconds} />}
        </section>
      ))}

      {/* Earlier sightings are per label, so they only make sense for a single match. */}
      {!several && pastSightings.length > 0 && (
        <section>
          <h3>Earlier sightings</h3>
          <ul className="item-list">
            {pastSightings.map((s) => (
              <li key={s.scan_id}>
                <strong>{friendlyTime(s.seen_at)}</strong>
                <span>{s.position}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  )
}
