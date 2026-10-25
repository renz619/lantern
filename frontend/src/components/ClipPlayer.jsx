import { useRef } from 'react'
import { fullUrl } from '../api'

// Plays a clip and starts two seconds early, because AI timestamps can be a bit off.
// The start time is set in the address (#t=) and on the player (currentTime)
// because phones honor one or the other. No autoplay: phones block it.
export default function ClipPlayer({ src, startSeconds = 0 }) {
  const ref = useRef(null)
  const start = Math.max(0, startSeconds - 2)
  const jump = () => {
    if (ref.current) ref.current.currentTime = start
  }

  return (
    <video
      ref={ref}
      className="preview"
      src={fullUrl(src) + '#t=' + start}
      controls
      playsInline
      preload="metadata"
      onLoadedMetadata={jump}
    />
  )
}
