import ClipPlayer from './ClipPlayer'

function friendlyTime(iso) {
  return new Date(iso).toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' })
}

export default function ResultCard({ item, pastSightings }) {
  return (
    <>
      <section className="card result">
        <h2>{item.label}</h2>
        <p className="position">{item.position}</p>
        <p>Last seen {friendlyTime(item.seen_at)}</p>
        <p>{item.description}</p>
        {item.clip_url && <ClipPlayer src={item.clip_url} startSeconds={item.clip_start_seconds} />}
      </section>

      {pastSightings.length > 0 && (
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
