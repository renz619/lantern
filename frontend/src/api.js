// The ONLY file that talks to the server
import { mockScans, mockScanDetail, mockFind, mockChanges } from './mocks'

const params = new URLSearchParams(window.location.search)
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true' || params.get('mock') === '1'
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function request(path, options) {
  const res = await fetch(BASE_URL + path, options)
  if (!res.ok) throw new Error('Server error ' + res.status)
  return res.json()
}

// Server paths look like /clips/12.mp4. Turn them into full web addresses.
export function fullUrl(path) {
  if (!path) return null
  return path.startsWith('http') ? path : BASE_URL + path
}

// The response shapes are still a proposal until B agrees. Each function below
// passes the reply through one of these, so if B names a field differently we
// fix it here and the screens keep reading the names in docs/contract.md.
const normalizeScan = (s) => ({
  id: s.id ?? s.scan_id,
  created_at: s.created_at ?? s.scanned_at,
  status: s.status,
  item_count: s.item_count ?? s.items?.length ?? 0,
})

const normalizeScanDetail = (s) => ({
  ...normalizeScan(s),
  error: s.error ?? null,
  video_url: s.video_url ?? null,
  items: s.items ?? [],
})

const normalizeFind = (r) => ({
  found: Boolean(r.found),
  item: r.item
    ? { ...r.item, seen_at: r.item.seen_at ?? r.item.scanned_at, clip_start_seconds: r.item.clip_start_seconds ?? 0 }
    : null,
  past_sightings: r.past_sightings ?? [],
  clarify: r.clarify ?? null,
})

const normalizeChanges = (c) => ({
  from_scan: c.from_scan ?? null,
  to_scan: c.to_scan ?? null,
  moved: c.moved ?? [],
  missing: c.missing ?? [],
  new: c.new ?? [],
})

export async function uploadScan(file) {
  if (USE_MOCKS) {
    await wait(800)
    return { scan_id: 99 }
  }
  const form = new FormData()
  form.append('video', file) // name must match B's endpoint
  return request('/scans', { method: 'POST', body: form })
}

export async function getScan(id) {
  if (USE_MOCKS) {
    await wait(500)
    return normalizeScanDetail(mockScanDetail(id))
  }
  return normalizeScanDetail(await request('/scans/' + id))
}

export async function listScans() {
  if (USE_MOCKS) {
    await wait(500)
    return mockScans.map(normalizeScan)
  }
  return (await request('/scans')).map(normalizeScan)
}

export async function findItem(q) {
  if (USE_MOCKS) {
    await wait(600)
    return normalizeFind(mockFind(q))
  }
  return normalizeFind(await request('/find?q=' + encodeURIComponent(q)))
}

export async function getChanges() {
  if (USE_MOCKS) {
    await wait(500)
    return normalizeChanges(mockChanges)
  }
  return normalizeChanges(await request('/changes'))
}
