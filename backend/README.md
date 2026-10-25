# Lantern backend

This folder contains Lantern's FastAPI server. FastAPI is the Python framework
that receives HTTP requests from the frontend and sends responses back.

## Requirements

- Python 3.11 or newer
- `pip`, Python's package installer

Check your Python version:

```bash
python3.11 --version
```

## One-time setup

Run these commands from `backend/`:

```bash
cd /Users/renzomarin/hack-tx/lantern/backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

A virtual environment (`.venv`) is an isolated place for this project's Python
packages. Activate it again with `source .venv/bin/activate` whenever you open a
new terminal.

## Start the development server

From `backend/`, with the virtual environment active:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`--reload` restarts the development server after Python files change. Verify the
server in a second terminal:

```bash
curl http://127.0.0.1:8000/health
```

Successful output:

```json
{"status":"ok"}
```

FastAPI's interactive API documentation is available at
<http://127.0.0.1:8000/docs> while the server is running.

## Scan upload and processing

The scan endpoints now use real local storage:

- `POST /scans` accepts a multipart field named `video`, saves it under a random
  server-generated filename, creates a SQLite scan, and starts analysis.
- `GET /scans` reads scan history from SQLite, newest first.
- `GET /scans/{id}` reads status and saved sightings from SQLite and includes a
  `video_url` when the uploaded file is available.
- `GET /media/scans/{id}/video` safely serves that scan's original video. It
  supports browser range requests, so a video player can seek to a sighting's
  `video_seconds` without downloading the entire file first.

Supported uploads are `.mp4`, `.mov`, `.webm`, and `.mkv`, up to 250 MB by
default. Configure storage and the size limit with:

```bash
export LANTERN_UPLOAD_DIR="/path/to/uploads"
export LANTERN_MAX_UPLOAD_BYTES=262144000
```

FastAPI runs analysis as a background task after accepting the upload. Select
the analyzer explicitly:

```bash
# Safe local default: deterministic fake items, no Gemini request
export LANTERN_ANALYZER=mock

# Real analysis: exceptions mark the scan failed and never fall back to fake data
export LANTERN_ANALYZER=gemini
export GEMINI_API_KEY="your-key-here"
```

`GEMINI_MOCK=1` is rejected when `LANTERN_ANALYZER=gemini`, which prevents a
real failure from appearing to be a fake success. Short ffmpeg-generated clips
are not created yet; the media URL plays and seeks within the original uploaded
video.

## Search and changes

`GET /find?q=` and `GET /changes` read the finished scans in SQLite and use member
A's code in `ai/` (`answer_question` and `diff_scans`, loaded by
`app/services/ai_tools.py`).

- `/find` looks at the newest scan that contained each label, so an item the latest
  scan missed is still found where it was last seen. Items sharing a label (two
  sets of keys) are all returned in `items`. A search that matches different labels
  returns `clarify` with the label names as options. For a single match,
  `past_sightings` lists up to five earlier scans only when they contain one item
  of that label with the same description (ignoring case and surrounding spaces).
  Ambiguous history is omitted. This is a conservative match, not a permanent
  identity for an object: descriptions changing between scans can shorten history.
  The newest scan containing a label supplies all current matches of that label;
  an older second set of keys is not carried forward once newer keys are found.
  `clip_url` is the scan's media URL and
  `clip_start_seconds` is the item's `video_seconds`.
- `/changes` compares the two newest finished scans (failed scans are skipped).
  With fewer than two it returns empty lists and `null` scan ids.

Both endpoints skip scans that are still `processing` or have `failed`. History
(`GET /scans`) includes every scan so the user can see pending and failed uploads.
A's search and diff functions run locally; neither endpoint spends Gemini quota.

## Repeatable demo seed (PDF Step 7)

A seed script fills the real SQLite tables with known sample records. These are
explicitly synthetic sightings, not Gemini results. The script never calls Gemini,
and real analysis failures never trigger the seed automatically.

From `backend/`, with the virtual environment active:

```bash
python -m app.scripts.seed_demo
```

Or from the repository root (the path used in the project outline):

```bash
backend/.venv/bin/python backend/scripts/seed_demo.py
```

Both commands default to the separate `backend/demo.sqlite`, even if
`LANTERN_DB_PATH` points at your real database. Successful output starts with:

```text
Synthetic demo data ready: morning scan 1, evening scan 2.
```

The script is idempotent, meaning running it again reuses the same records and
does not create duplicates. It refuses a database containing unmarked user scans,
preserves scans uploaded after seeding, and copies any supplied videos without
altering their source files. A failed seed rolls back its new database records
and removes the video copies it created. Nothing is deleted from your real scans.

To start the server using the demo database, run from `backend/`:

```bash
export LANTERN_DB_PATH="/Users/renzomarin/hack-tx/lantern/backend/demo.sqlite"
export LANTERN_ANALYZER=mock
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In <http://127.0.0.1:8000/docs>, expand an endpoint, choose **Try it out**, fill
any parameters, and choose **Execute**. Expect:

| Request | Expected demo behavior |
| --- | --- |
| `GET /scans` | Evening scan then morning scan; three sightings each |
| `GET /find?q=keys` | Keys on the nightstand; earlier sighting on the desk |
| `GET /find?q=wallet` | Wallet last seen on the dresser in the morning |
| `GET /changes` | Keys moved; wallet missing; phone new |

In this default demo, media URLs are `null`: there are no bundled or invented
video files. For playback, supply **both** local videos on the first seed:

```bash
python -m app.scripts.seed_demo \
  --database demo-with-video.sqlite \
  --morning-video "/absolute/path/to/morning.mp4" \
  --evening-video "/absolute/path/to/evening.mov"
```

Use your own existing paths. The videos are copied into `LANTERN_UPLOAD_DIR`
(default `backend/uploads/`) and served through the existing media endpoint.
Keep the same upload directory when starting the server, and set
`LANTERN_DB_PATH` to the absolute path of `demo-with-video.sqlite`.
Stage recordings to match the sample scenes: morning keys on the desk at 4.5s,
wallet on the dresser at 8s; evening keys on the nightstand at 9.2s, phone on the
bed at 11.2s; blue water bottle on the table at 12s in both. The seed does not
analyze or verify video contents. Arbitrary videos will not match its fake data.

Rerunning a seed keeps its existing records and videos. If you first seeded
without videos, choose a new empty database path to create a demo with playback.
Database and upload files are ignored by Git; the seed source code is committed.

To return to your real local database, stop the server with **Ctrl+C**, then:

```bash
unset LANTERN_DB_PATH
export LANTERN_ANALYZER=gemini
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

This uses `backend/lantern.sqlite`. Supply the Gemini key in the server's
environment as usual. Keep the demo database setting for a demo on Render as
well; a local seed does not populate the deployed service automatically.

## SQLite storage checkpoint

`app/database.py` defines the real local storage layer. SQLite is a database kept
in one file, so it does not need a separate database server.

The database has two tables:

- `scans` stores when each scan started, its status, video path, and any error.
- `sightings` stores every detected item and links it to the scan that found it.

The default database path is `backend/lantern.sqlite`. Override it when needed:

```bash
export LANTERN_DB_PATH="/path/to/another.sqlite"
```

Database files are ignored by Git. Tests use temporary databases and never touch
the default file.

## Frontend access (CORS)

CORS is the browser permission policy that controls which website addresses may
call this server. Lantern allows Vite's default development addresses:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

To use different addresses, provide a comma-separated environment variable
before starting the server:

```bash
export LANTERN_CORS_ORIGINS="https://example-frontend.test,http://localhost:5173"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Run tests

From `backend/`, with the virtual environment active:

```bash
python -m pytest -q
```

A successful run currently ends with `50 passed`. Tests use temporary storage
and do not make Gemini API requests.
