import { useState } from 'react'
import Loading from './Loading'
import { getScan } from '../api'

const STATUS_LABELS = { processing: 'Processing', done: 'Done', failed: 'Failed' }

function formatDate(iso) {
  return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

export default function ScanCard({ scan }) {
  const [open, setOpen] = useState(false)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)

  async function toggle() {
    const opening = !open
    setOpen(opening)
    // Load the item list on first open, and again if it wasn't ready yet.
    if (!opening || loading || detail?.status === 'done') return
    setLoading(true)
    setFailed(false)
    try {
      setDetail(await getScan(scan.id))
    } catch {
      setFailed(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <li className="scan-card">
      <button className="scan-header" onClick={toggle} aria-expanded={open}>
        <span>
          <strong>{formatDate(scan.created_at)}</strong>
          <span className="muted"> · {scan.item_count} items</span>
        </span>
        <span className={'badge ' + scan.status}>{STATUS_LABELS[scan.status] || scan.status}</span>
      </button>

      {open && (
        <div className="scan-body">
          {loading && <Loading>Loading…</Loading>}
          {failed && <p role="alert" className="warning">Couldn’t load this scan. Try again.</p>}
          {detail && detail.status !== 'done' && !loading && (
            <p>This scan isn’t ready yet. Close it and tap again in a moment.</p>
          )}
          {detail?.status === 'done' && (
            <ul className="item-list">
              {detail.items.map((item, i) => (
                <li key={item.label + i}>
                  <strong>{item.label}</strong>
                  <span>{item.position}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </li>
  )
}
