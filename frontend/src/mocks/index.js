import scans from './scans.json'
import scanDetail from './scan-detail.json'
import find from './find.json'
import changes from './changes.json'

export const mockScans = scans
export const mockChanges = changes

// Scans start as "processing" and become "done" on the third check,
// so the progress screen can be tested.
const checks = {}

export function mockScanDetail(id) {
  checks[id] = (checks[id] || 0) + 1
  if (checks[id] < 3) {
    return { id: Number(id), created_at: scanDetail.created_at, status: 'processing', error: null, video_url: null, items: [] }
  }
  return { ...scanDetail, id: Number(id) }
}

export function mockFind(q) {
  const query = q.trim().toLowerCase()
  if (query.includes('charger')) {
    return {
      found: true,
      items: [],
      past_sightings: [],
      clarify: { question: 'Which charger?', options: ['phone charger', 'laptop charger'] },
    }
  }
  const matches = scanDetail.items.filter((i) => i.label.includes(query) || query.includes(i.label))
  if (!query || matches.length === 0) return { found: false, items: [], past_sightings: [], clarify: null }
  return {
    ...find,
    items: matches.map((match) => ({
      ...find.items[0],
      ...match,
      scan_id: scanDetail.id,
      seen_at: scanDetail.created_at,
      clip_start_seconds: match.video_seconds,
    })),
  }
}
