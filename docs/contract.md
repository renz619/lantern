# API contract

This is the agreement between the frontend (C), backend (B) and AI code (A). **Only change it after telling everyone.**

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
| `label` | The item's name, from our standard list of names (so "earbuds" and "headphones" don't become two items) |
| `description` | Short description of this specific item |
| `anchor` | The nearby furniture (never tracked as an item itself) |
| `position` | The sentence we show people |
| `confidence` | How sure the AI is, 0 to 1. Guesses below the cutoff are dropped |
| `video_seconds` | Seconds into the video where the item was seen |

## Endpoints

| Endpoint | You send | You get back |
| --- | --- | --- |
| `GET /health` | Nothing | A page that says the server is alive |
| `POST /scans` | A video file | A scan ID number; the backend analyzes the video in the background |
| `GET /scans` | Nothing | A list of all scans, by date |
| `GET /scans/{id}` | Nothing | The status of one scan and everything found in it |
| `GET /find?q=keys` | A search word | Where the item was last seen, when, a link to the video clip, and past sightings |
| `GET /changes` | Nothing | What moved, went missing, or is new since the previous scan |

## Functions A provides to B

- `analyze_video(path, watchlist)` returns a list of items (shape above). `watchlist` is the user's extra items to look for.
- `answer_question(items, query)` handles fuzzy search ("charger" matches "phone charger") and asks a follow-up if a search could mean two things.
- `diff_scans(old, new)` returns items that moved, went missing, or are new.

## Open details (agree on these before building against them)

The outline fixes the item shape and the endpoint list, but not the exact response bodies. Fill these in as a team, then update this file:

- [ ] Scan status values (for example `processing`, `done`, `failed`)
- [ ] Response shape of `POST /scans`, `GET /scans`, `GET /scans/{id}`
- [ ] Response shape of `GET /find` (last sighting, `scanned_at`, `clip_url`, `past_sightings`, follow-up question)
- [ ] Response shape of `GET /changes` (`moved`, `missing`, `new`)
- [ ] How the video clip URL is served and how the frontend jumps to `video_seconds`
