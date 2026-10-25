// A spinner plus a message. Screen readers announce the message only.
export default function Loading({ children }) {
  return (
    <p role="status" className="status">
      <span className="spinner" aria-hidden="true" />
      {children}
    </p>
  )
}
