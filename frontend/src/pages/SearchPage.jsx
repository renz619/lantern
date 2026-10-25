import { useRef, useState } from 'react'
import ResultCard from '../components/ResultCard'
import { findItem } from '../api'

const CHIPS = ['keys', 'wallet', 'phone', 'charger', 'glasses']

export default function SearchPage({ goTo }) {
  const [query, setQuery] = useState('')
  // 'idle', 'loading', 'found', 'clarify', 'notfound' or 'error'
  const [state, setState] = useState('idle')
  const [result, setResult] = useState(null)
  const latest = useRef(0) // ignores replies from older searches

  async function search(text) {
    const q = text.trim()
    if (!q) return
    setQuery(q)
    setState('loading')
    const id = ++latest.current
    try {
      const reply = await findItem(q)
      if (id !== latest.current) return
      setResult(reply)
      if (reply.clarify) setState('clarify')
      else setState(reply.found && reply.item ? 'found' : 'notfound')
    } catch {
      if (id !== latest.current) return
      setState('error')
    }
  }

  function submit(e) {
    e.preventDefault()
    search(query)
  }

  return (
    <>
      <h1>Where is it?</h1>

      <form className="search-form" onSubmit={submit}>
        <input
          type="search"
          aria-label="Item to find"
          placeholder="keys, wallet, phone…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="primary" disabled={state === 'loading'}>
          Search
        </button>
      </form>

      <div className="chips">
        {CHIPS.map((chip) => (
          <button key={chip} onClick={() => search(chip)} disabled={state === 'loading'}>
            {chip}
          </button>
        ))}
      </div>

      {state === 'loading' && <p role="status" className="status">Looking for “{query}”…</p>}

      {state === 'found' && (
        <ResultCard item={result.item} pastSightings={result.past_sightings} />
      )}

      {state === 'clarify' && (
        <section className="card">
          <strong>{result.clarify.question}</strong>
          <div className="actions">
            {result.clarify.options.map((option) => (
              <button key={option} onClick={() => search(option)}>{option}</button>
            ))}
          </div>
        </section>
      )}

      {state === 'notfound' && (
        <section className="card">
          <p>We haven’t seen that yet. Try scanning again.</p>
          <button className="primary" onClick={() => goTo('scan')}>Go to Scan</button>
        </section>
      )}

      {state === 'error' && (
        <p role="alert" className="warning">
          Couldn’t reach the server. Check your connection and try again.
        </p>
      )}
    </>
  )
}
