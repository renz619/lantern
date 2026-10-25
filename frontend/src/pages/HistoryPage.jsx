import { useEffect, useState } from 'react'
import ChangeSummary from '../components/ChangeSummary'
import ScanCard from '../components/ScanCard'
import { getChanges, listScans } from '../api'

export default function HistoryPage({ goTo }) {
  // 'loading', 'ready' or 'error'
  const [state, setState] = useState('loading')
  const [scans, setScans] = useState([])
  const [changes, setChanges] = useState(null)

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
        <h1>History</h1>
        <p role="status" className="status">Loading your scans…</p>
      </>
    )
  }

  if (state === 'error') {
    return (
      <>
        <h1>History</h1>
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
        <h1>History</h1>
        <section className="card">
          <p>No scans yet. Go to Scan and film your room.</p>
          <button className="primary" onClick={() => goTo('scan')}>Go to Scan</button>
        </section>
      </>
    )
  }

  return (
    <>
      <h1>History</h1>
      {scans.length === 1 ? (
        <section className="card">
          <p>Scan again later to see what changed.</p>
        </section>
      ) : (
        <ChangeSummary changes={changes} />
      )}
      <h2>Your scans</h2>
      <ul className="timeline">
        {scans.map((scan) => (
          <ScanCard key={scan.id} scan={scan} />
        ))}
      </ul>
    </>
  )
}
