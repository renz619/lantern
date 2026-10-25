import { useEffect, useRef, useState } from 'react'
import Loading from '../components/Loading'
import ResultCard from '../components/ResultCard'
import { findItem } from '../api'

const CHIPS = ['keys', 'wallet', 'phone', 'charger', 'glasses']

// Voice search uses the browser's speech recognition. Support varies by browser
// (and may need HTTPS), so the mic button is hidden when it isn't there.
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
const voiceSupported = Boolean(SpeechRecognition)

// Results are read aloud with the browser's speech synthesis.
const speechSupported = 'speechSynthesis' in window

// Browsers ship a mix of voices; neural/"natural" ones sound far better than the default.
function voiceScore(v) {
  if (!v.lang.startsWith('en')) return -1
  let score = v.lang === 'en-US' ? 1 : 0
  if (/natural|neural/i.test(v.name)) score += 10 // Edge "Online (Natural)" voices
  if (/premium|enhanced/i.test(v.name)) score += 6 // macOS / iOS
  if (/google/i.test(v.name)) score += 4 // Chrome
  if (/aria|jenny|samantha|ava|zoe/i.test(v.name)) score += 2
  if (!v.localService) score += 1 // cloud voices are usually better
  return score
}

function bestVoice() {
  const voices = window.speechSynthesis.getVoices()
  return voices.reduce((best, v) => (voiceScore(v) > (best ? voiceScore(best) : -1) ? v : best), null)
}

function speak(text) {
  if (!speechSupported) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  const voice = bestVoice() // voices load async, so look up at speak time
  if (voice) utterance.voice = voice
  utterance.lang = voice ? voice.lang : 'en-US'
  utterance.rate = 0.95
  window.speechSynthesis.speak(utterance)
}

function spokenResult(reply) {
  if (reply.clarify) return reply.clarify.question
  if (reply.found && reply.items.length === 1) {
    const [item] = reply.items
    return `Found your ${item.label}. ${item.position}. ${item.description}`
  }
  if (reply.found && reply.items.length > 1) {
    const found = reply.items
      .map((item, i) => `${i === 0 ? 'First' : 'Next'}, ${item.description}, ${item.position}.`)
      .join(' ')
    return `I found ${reply.items.length} matches. ${found}`
  }
  return 'We haven’t seen that yet. Try scanning your room again.'
}

export default function SearchPage({ goTo }) {
  const [query, setQuery] = useState('')
  // 'idle', 'loading', 'found', 'clarify', 'notfound' or 'error'
  const [state, setState] = useState('idle')
  const [result, setResult] = useState(null)
  const latest = useRef(0) // ignores replies from older searches
  const [listening, setListening] = useState(false)
  const [voiceError, setVoiceError] = useState('')

  useEffect(() => () => speechSupported && window.speechSynthesis.cancel(), [])

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
      speak(spokenResult(reply))
      if (reply.clarify) setState('clarify')
      else setState(reply.found && reply.items.length > 0 ? 'found' : 'notfound')
    } catch {
      if (id !== latest.current) return
      setState('error')
    }
  }

  function listen() {
    setVoiceError('')
    const rec = new SpeechRecognition()
    rec.lang = 'en-US'
    rec.onresult = (event) => search(event.results[0][0].transcript)
    rec.onerror = () => setVoiceError('Couldn’t hear that. Try again or type your search.')
    rec.onend = () => setListening(false)
    setListening(true)
    try {
      rec.start()
    } catch {
      setListening(false)
    }
  }

  function submit(e) {
    e.preventDefault()
    search(query)
  }

  return (
    <>
      <h1>What are you looking for?</h1>
      <p className="lede">Type it, say it, or tap a quick pick below.</p>

      <form className="search-form" onSubmit={submit}>
        <label className="field-label" htmlFor="item-query">Item to find</label>
        <input
          id="item-query"
          type="search"
          placeholder="Try “keys” or “wallet”"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {voiceSupported && (
          <button type="button" onClick={listen} disabled={listening} aria-label="Search by voice">
            {listening ? 'Listening…' : 'Voice'}
          </button>
        )}
        <button type="submit" className="primary" disabled={state === 'loading'}>
          Search
        </button>
      </form>
      {voiceError && <p role="alert" className="warning">{voiceError}</p>}

      <div className="chips" role="group" aria-label="Quick picks">
        {CHIPS.map((chip) => (
          <button key={chip} onClick={() => search(chip)} disabled={state === 'loading'}>
            {chip}
          </button>
        ))}
      </div>

      {speechSupported && result && (state === 'found' || state === 'clarify' || state === 'notfound') && (
        <button type="button" onClick={() => speak(spokenResult(result))}>Read aloud again</button>
      )}

      {state === 'loading' && <Loading>Looking for “{query}”…</Loading>}

      {state === 'found' && (
        <ResultCard items={result.items} pastSightings={result.past_sightings} />
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
          <p>We haven’t seen that yet. Try scanning your room again, and make sure it’s in view.</p>
          <button className="primary" onClick={() => goTo('scan')}>Scan your room</button>
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
