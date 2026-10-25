# API contract

This is the agreement between the frontend (C), backend (B) and AI code (A).
The response formats below document the current implementation, including the
Step 6 history rule. **Coordinate changes with the team before changing this file.**

Requests and responses use JSON unless noted otherwise. Scan IDs are integers.
Dates such as `created_at` and `seen_at` are UTC timestamps in ISO 8601 format,
for example `2026-10-24T18:00:00Z`. Arrays are always present, even when empty;
nullable fields are present as `null`. The backend's schema definitions are in
[`backend/app/schemas.py`](../backend/app/schemas.py).

## The item

Every item found in a video looks like this:

```json
{
  "label": "keys",
  "description": "silver keys on a blue lanyard",
  "anchor": "desk",
  "position": "on the desk, left of the monitor",
  "confidence": 0.87,
  "video_seconds": 14.5
}
```

| Field | Meaning |
| --- | --- |
| `label` | Standard item name, normalized using A's vocabulary and aliases; multi-word names retain spaces |
| `description` | Short description of this specific item |
| `anchor` | The nearby furniture (never tracked as an item itself) |
| `position` | The sentence we show people |
| `confidence` | How sure the AI is, 0 to 1. Guesses below the cutoff are dropped |
| `video_seconds` | Nonnegative number of seconds into the original video where the item was seen |

The item has exactly these six fields. Search matches add the four fields
documented under `/find`; scan-detail items keep the six-field shape.

## Standard labels and anchors

[`ai/vocabulary.json`](../ai/vocabulary.json), owned by A, defines `labels`,
`aliases`, `anchors`, and `anchor_aliases`. Refer to it rather than keeping
separate lists in the backend and frontend.

- Names are lowercase with surrounding spaces removed. Multi-word labels such as
  `water bottle`, `power bank`, and `usb drive` are supported as single strings.
- Aliases normalize equivalent names: `key` becomes `keys`, and `bottle` becomes
  `water bottle`. `earbuds` and `headphones`, and `pen` and `pencil`, remain
  distinct labels. Not every word in `labels` is necessarily returned unchanged:
  the current aliases map `earbud case` to `earbuds`.
- The watchlist permits additional normalized labels outside the built-in list.
- Furniture is used as an anchor, never tracked as an item. Anchor synonyms such
  as `sofa` normalize to `couch`. A currently preserves unknown anchor words;
  the backend does not reject them as an enum (a closed set of allowed values).
- A applies the confidence cutoff before returning items; the current default is
  `0.5`. The API accepts confidence values from `0` through `1`.

## Endpoints

| Endpoint | You send | You get back |
| --- | --- | --- |
| `GET /health` | Nothing | `{"status":"ok"}` |
| `POST /scans` | Multipart video and optional watchlist | HTTP 202 and `{"scan_id": 1}`; analysis runs in the background |
| `GET /scans` | Nothing | A list of all scans, by date |
| `GET /scans/{id}` | Nothing | The status of one scan and everything found in it |
| `GET /find?q=keys` | A search word | Where the item was last seen, when, a link to the video clip, and past sightings |
| `GET /changes` | Nothing | What moved, went missing, or is new since the previous scan |
| `GET /media/scans/{id}/video` | A scan ID; optional HTTP `Range` header | The original uploaded video, or 404 if unavailable |

## Scan endpoints

### `POST /scans`

Send `multipart/form-data` (a form containing a file), not JSON:

- `video`: required file field, with a filename ending in `.mp4`, `.mov`,
  `.webm`, or `.mkv` (case insensitive).
- `watchlist`: optional repeated text fields, one item name per field. Omit the
  field when there is no watchlist; the current frontend sends only `video`.

The file must be nonempty. The default limit is 262,144,000 bytes (250 MiB),
configurable through `LANTERN_MAX_UPLOAD_BYTES`. Extension checks are not a
guarantee that the file contains valid video. Aim for 30–60 second recordings;
the backend does not enforce that duration yet.

Successful response: **202 Accepted**, meaning upload accepted, not analysis
completed:

```json
{"scan_id": 1}
```

The backend saves the file, creates a `processing` scan, and schedules analysis.
The frontend polls `GET /scans/{id}` until the status is `done` or `failed`.

| Status | Meaning |
| --- | --- |
| `processing` | Accepted; analysis has not finished |
| `done` | Analysis succeeded and sightings were saved; `items` may be empty |
| `failed` | Analysis or saving failed; `error` explains the failure |

A failure is not replaced by fake results. `LANTERN_ANALYZER=mock` is an explicit
development choice; `gemini` runs real analysis. The seed script inserts
explicitly synthetic demo data only when manually invoked, never as a fallback.

### `GET /scans`

Returns **200 OK** with an array, newest first by `created_at`, then descending
ID to break ties. Includes `processing`, `done`, and `failed` scans.
An empty database returns `[]`.

```json
[
  {"id": 2, "created_at": "2026-10-24T18:00:00Z", "status": "done", "item_count": 3},
  {"id": 1, "created_at": "2026-10-24T09:00:00Z", "status": "done", "item_count": 3}
]
```

`item_count` is the nonnegative number of saved sightings, not a predicted total.

### `GET /scans/{id}`

Returns **200 OK** with these fields. Items are ordered by `video_seconds`,
with insertion order breaking ties.

```json
{
  "id": 2,
  "created_at": "2026-10-24T18:00:00Z",
  "status": "done",
  "error": null,
  "video_url": "/media/scans/2/video",
  "items": [
    {
      "label": "keys",
      "description": "silver keys on a blue lanyard",
      "anchor": "nightstand",
      "position": "on the nightstand",
      "confidence": 0.9,
      "video_seconds": 9.2
    }
  ]
}
```

`video_url` is `null` if no accessible uploaded file exists, including a seed
created without videos. Its presence does not imply analysis succeeded; an
upload can still be playable while its scan is `processing` or `failed`.
`error` is normally `null`; a failed background analysis stores an error string.

## Search: `GET /find?q=`

`q` is a required, nonempty query string. The backend searches only `done` scans
and calls A's local `answer_question` function; searching does not call Gemini.

For each label, candidates come from the newest completed scan containing that
label. If the latest scan missed a wallet, search can still return its older
last-known location. This selection is by label, not by permanent object ID:
if a newer scan contains one set of keys, an older second set is not carried
forward as an additional current match.

### Found

Returns **200 OK**. Each entry in `items` has the six item fields plus
`scan_id`, `seen_at`, `clip_url`, and `clip_start_seconds`:

```json
{
  "found": true,
  "items": [
    {
      "label": "keys",
      "description": "silver keys on a blue lanyard",
      "anchor": "nightstand",
      "position": "on the nightstand",
      "confidence": 0.9,
      "video_seconds": 9.2,
      "scan_id": 2,
      "seen_at": "2026-10-24T18:00:00Z",
      "clip_url": "/media/scans/2/video",
      "clip_start_seconds": 9.2
    }
  ],
  "past_sightings": [
    {"scan_id": 1, "seen_at": "2026-10-24T09:00:00Z", "position": "on the desk"}
  ],
  "clarify": null
}
```

`seen_at` is the scan's creation timestamp, not the video timestamp. The canonical
date fields are `created_at` for scans and `seen_at` for sightings; the backend
does not send `scanned_at`.

### Not found

No scans, no match, or a whitespace-only query returns **200 OK**, not 404:

```json
{"found": false, "items": [], "past_sightings": [], "clarify": null}
```

### Clarification

If the query matches different labels, return **200 OK** with `found: true`,
empty `items`, and a follow-up question. The UI must inspect `clarify` before
treating `found` as a final answer.

```json
{
  "found": true,
  "items": [],
  "past_sightings": [],
  "clarify": {
    "question": "Did you mean your headphones or your airpods?",
    "options": ["headphones", "airpods"]
  }
}
```

Options are label strings. Choosing an option sends another `GET /find?q=` with
that label. The HTTP API does not currently expose A's numeric `choice` argument.

### Several items with the same label and their history

A room can hold two sets of keys. Same-label matches are returned together in
`items`, with `clarify: null`; descriptions help users distinguish them. The
canonical response uses an `items` array, even for one match. The frontend's
support for the older single `item` shape is compatibility code only.

`past_sightings` is populated only for a single returned match. It contains at
most five earlier completed scans, newest first, and each entry has exactly
`scan_id`, `seen_at`, and `position`. An older scan qualifies only if it has
exactly one item of that label and its description matches the current match
after removing surrounding whitespace and ignoring case. A blank description,
multiple same-label items, or a changed description produces no history entry
for that scan. This conservative rule can omit real history and does not prove
physical identity. Permanent item IDs remain future work.

## Changes: `GET /changes`

Compares the two newest `done` scans using A's local `diff_scans`, skipping
`processing` and `failed` scans. Returns **200 OK**:

```json
{
  "from_scan": 1,
  "to_scan": 2,
  "moved": [
    {"label": "keys", "description": "silver keys on a blue lanyard", "from_position": "on the desk", "to_position": "on the nightstand"}
  ],
  "missing": [
    {"label": "wallet", "description": "brown leather wallet", "last_position": "on the dresser"}
  ],
  "new": [
    {"label": "phone", "description": "black phone in a clear case", "position": "on the bed"}
  ]
}
```

With fewer than two completed scans, both IDs are `null` and all arrays are empty:

```json
{"from_scan": null, "to_scan": null, "moved": [], "missing": [], "new": []}
```

### What "moved" means

`diff_scans(old, new)` in `ai/diff.py`:

1. Items are paired within the same `label`. If each scan has exactly one, they are paired. Otherwise the best matches by `description` similarity (plus a bonus for the same `anchor`) are paired, and weak matches are not.
2. A paired item **moved** if its `anchor` changed. We compare `anchor`, not `position`, because the AI words the position sentence differently each run.
3. An old item with no pair is **missing**. A new item with no pair is **new**.

These are estimates based on detections: "missing" means not paired in the newer
scan, not proof that an item was physically removed. Change pairing uses A's
similarity logic; it is separate from the stricter search-history rule above.

## Media URLs and playback

`video_url` and `clip_url` currently point to the **original uploaded video** at
`/media/scans/{id}/video`. Short ffmpeg clips and stills are not generated yet.
URLs are relative to the backend's base address. The frontend prefixes the API
base in development; when the backend serves the site, they use the same origin.

- `clip_start_seconds` currently equals `video_seconds`, measured from the
  original video's start. Do not subtract any lead-in time in the backend.
- The frontend player starts at `max(0, clip_start_seconds - 2)` to give two
  seconds of context. It uses both the URL fragment `#t=` and `currentTime`.
- The media route supports `Range` requests: the browser can request part of a
  file for seeking. Full reads return 200; valid byte ranges return 206.
- The response content type follows the file extension (for example `video/mp4`
  or `video/quicktime`). Actual playback depends on the browser's codec support;
  the backend does not transcode uploads yet.
- Missing scans, missing files, or paths outside the configured upload directory
  return 404. A media URL never exposes a local filesystem path.
- Null URLs mean media is unavailable; the frontend should omit the player.

If shortened clips are introduced later, coordinate their timestamp semantics
first: offsets within a shortened clip differ from offsets in the source video.

## Errors

| HTTP status | Current behavior |
| --- | --- |
| 400 | Missing video filename or empty upload |
| 404 | Unknown scan (`Scan not found`) or unavailable media (`Video not found`) |
| 413 | Upload exceeds the configured size limit (`Video is too large`) |
| 415 | Unsupported filename extension (`Unsupported video type`) |
| 422 | Request validation failed, such as missing `video`, missing/empty `q`, or a non-integer scan ID |

Explicit route errors return a JSON `detail` string. FastAPI's 422 responses have
a `detail` array describing invalid fields. A background Gemini failure does not
retroactively change the upload's 202 response; poll the scan status to see it.

## Functions A provides to B

- `analyze_video(path, watchlist=None)` is synchronous (called without `await`)
  and returns a list of six-field items. Real failures raise exceptions. The
  backend adapter selects mock or real analysis explicitly and stores failures.
- `answer_question(items, query, choice=None)` performs local fuzzy search and
  returns `status` (`found`, `ambiguous`, or `not_found`), `message`, `matches`,
  `question`, and `choices`. The backend translates this into the HTTP
  `found/items/past_sightings/clarify` format; A's result is not the HTTP response.
- `diff_scans(old, new)` accepts two lists of items and returns `moved`,
  `missing`, and `new` arrays. The backend adds `from_scan` and `to_scan`.

## Decisions recorded and remaining work

- [x] Scan statuses: `processing`, `done`, `failed`.
- [x] Exact response bodies for scan upload, history, and detail.
- [x] Search list, clarification, timestamps, and conservative past-sighting rule.
- [x] Changes response and insufficient-scan behavior.
- [x] Original-video URLs and original-video timestamp seeking.

Future changes require coordination: permanent identity across scans, shortened
clip offsets, deletion endpoints, and any changed response fields. Authentication
and scan deletion are not currently implemented; do not imply they already work.
