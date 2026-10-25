import { useEffect, useState } from 'react'
import ChangeSummary from '../components/ChangeSummary'
import Loading from '../components/Loading'
import ScanCard from '../components/ScanCard'
import { getChanges, listScans } from '../api'

export default function HistoryPage({ goTo }) {
  // 'loading', 'ready' or 'error'
  const [state, setState] = useState('loading')
  const [scans, setScans] = useState([])
  const [changes, setChanges] = useState(null)

  const [showScans, setShowScans] = useState(false) // previous scans start collapsed
  const [attempt, setAttempt] = useState(0) // bump to load again

  useEffect(() => {
    let cancelled = false
    Promise.all([listScans(), getChanges()])
      .then(([scanList, changeList]) => {
        if (cancelled) return
        // Newest first
        setScans([...scanList].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)))
        setChanges(changeList)
        setState('ready')
      })
      .catch(() => {
        if (!cancelled) setState('error')
      })
    return () => {
      cancelled = true
    }
  }, [attempt])

  if (state === 'loading') {
    return (
      <>
        <h1>Your history</h1>
        <Loading>Loading your scans…</Loading>
      </>
    )
  }

  if (state === 'error') {
    return (
      <>
        <h1>Your history</h1>
        <p role="alert" className="warning">Couldn’t reach the server. Check your connection and try again.</p>
        <button
          className="primary"
          onClick={() => {
            setState('loading')
            setAttempt((n) => n + 1)
          }}
        >
          Try again
        </button>
      </>
    )
  }

  if (scans.length === 0) {
    return (
      <>
        <h1>Your history</h1>
        <section className="card">
          <p>No scans yet. Film your room and we’ll start remembering where your things are.</p>
          <button className="primary" onClick={() => goTo('scan')}>Scan your room</button>
        </section>
      </>
    )
  }

  return (
    <>
      <h1>Your history</h1>
      {scans.length === 1 ? (
        <section className="card">
          <p>Nice start! Scan again later and we’ll show you what moved.</p>
        </section>
      ) : (
        <ChangeSummary changes={changes} />
      )}
      <button
        className="dropdown-toggle"
        onClick={() => setShowScans((open) => !open)}
        aria-expanded={showScans}
        aria-controls="previous-scans"
      >
        <span>Previous scans ({scans.length})</span>
        <span aria-hidden="true">{showScans ? '▲' : '▼'}</span>
      </button>
      {showScans && (
        <ul id="previous-scans" className="timeline scroll-list">
          {scans.map((scan) => (
            <ScanCard key={scan.id} scan={scan} />
          ))}
        </ul>
      )}
    </>
  )
}
