import { useEffect, useMemo, useRef, useState } from 'react'
import Loading from '../components/Loading'
import TipsCard from '../components/TipsCard'
import { uploadScan, getScan } from '../api'

const BIG_FILE_BYTES = 150 * 1024 * 1024
const POLL_MS = 2500
const MAX_POLLS = 120

const MESSAGES = {
  uploading: 'Uploading…',
  analyzing: 'Gemini is watching your video…',
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

export default function ScanPage({ goTo }) {
  const inputRef = useRef(null)
  const mounted = useRef(true)
  const [file, setFile] = useState(null)
  // 'idle' (nothing happening), 'uploading', 'analyzing', 'done' or 'error'
  const [phase, setPhase] = useState('idle')
  const [items, setItems] = useState([])
  const [error, setError] = useState('')

  // Preview address for the chosen video; released when the file changes.
  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])
  useEffect(() => () => previewUrl && URL.revokeObjectURL(previewUrl), [previewUrl])

  // Stop updating the screen if the user leaves the Scan tab mid-scan.
  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  function choose(e) {
    const picked = e.target.files[0]
    e.target.value = '' // lets the same file be picked again
    if (!picked) return
    setFile(picked)
    setPhase('idle')
    setError('')
  }

  async function analyze() {
    setPhase('uploading')
    setError('')
    try {
      const { scan_id } = await uploadScan(file)
      if (!mounted.current) return
      setPhase('analyzing')
      for (let attempt = 0; attempt < MAX_POLLS; attempt++) {
        const scan = await getScan(scan_id)
        if (!mounted.current) return
        if (scan.status === 'done') {
          setItems(scan.items)
          setPhase('done')
          return
        }
        if (scan.status === 'failed') throw new Error(scan.error || 'Analysis failed')
        await wait(POLL_MS)
      }
      throw new Error('Analysis took too long')
    } catch {
      if (!mounted.current) return
      setError("Something went wrong while scanning. Check your connection and try again.")
      setPhase('error')
    }
  }

  function reset() {
    setFile(null)
    setItems([])
    setPhase('idle')
    setError('')
  }

  const busy = phase === 'uploading' || phase === 'analyzing'

  return (
    <>
      <h1>Scan your room</h1>
      {phase === 'idle' && (
        <p className="lede">Film a slow spin around the room and we’ll remember where everything is.</p>
      )}
      {phase === 'idle' && <TipsCard />}

      <input
        type="file"
        accept="video/*"
        capture="environment"
        ref={inputRef}
        hidden
        onChange={choose}
      />

      {phase !== 'done' && !file && (
        <button className="primary block" onClick={() => inputRef.current.click()}>
          Record room video
        </button>
      )}

      {phase !== 'done' && file && (
        <>
          <video className="preview" src={previewUrl} controls playsInline aria-label="Preview of your room video" />
          {file.size > BIG_FILE_BYTES && (
            <p className="warning">This video is large and may take a while to upload.</p>
          )}
          {busy ? (
            <Loading>{MESSAGES[phase]}</Loading>
          ) : (
            <div className="actions">
              <button className="primary" onClick={analyze}>
                {phase === 'error' ? 'Retry' : 'Analyze'}
              </button>
              <button onClick={() => inputRef.current.click()}>Choose a different video</button>
            </div>
          )}
          {phase === 'error' && <p role="alert" className="warning">{error}</p>}
        </>
      )}

      {phase === 'done' && (
        <>
          <h2>All done! We found {items.length} {items.length === 1 ? 'item' : 'items'}.</h2>
          <ul className="item-list">
            {items.map((item) => (
              <li key={item.label}>
                <strong>{item.label}</strong>
                <span>{item.position}</span>
              </li>
            ))}
          </ul>
          <div className="actions">
            <button className="primary" onClick={() => goTo('search')}>Search for something</button>
            <button onClick={reset}>Scan again</button>
          </div>
        </>
      )}
    </>
  )
}
