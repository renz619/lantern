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

A successful run ends with `2 passed`.
