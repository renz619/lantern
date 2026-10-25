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

## Mock API checkpoint

The current endpoints return predictable fake data so the frontend and backend
can be tested together before the database and Gemini integration exist:

- `POST /scans` accepts a multipart field named `video` and returns scan ID `99`.
- `GET /scans` returns the mock scan history, newest first.
- `GET /scans/{id}` returns scan status and items. Scan `99` changes from
  `processing` to `done` on its third status check.
- `GET /find?q=keys` returns every matching item, including duplicate labels.
- `GET /changes` returns mock moved, missing, and new items.

The mock upload is not written to disk and is not sent to Gemini. Those behaviors
belong to later checkpoints.

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
the default file. The API routes still use mock data in this checkpoint; later
work will connect these tested database operations to uploads and analysis.

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

A successful run currently ends with `16 passed`.
