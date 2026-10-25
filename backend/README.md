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
real failure from appearing to be a fake success. `GET /find` and `GET /changes`
still return mock responses. Short ffmpeg-generated clips are not created yet;
the current media URL plays and seeks within the original uploaded video.

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

A successful run currently ends with `30 passed`.
