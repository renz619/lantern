# AGENTS.md

## What this project does

Lantern is a mobile-friendly web app that remembers where you put your stuff. The user films a slow spin around a room. Gemini watches the video and lists the small movable items it sees (keys, wallet, phone...) with where each one is, using furniture as location words ("on the desk, left of the monitor"). The backend saves each scan with a timestamp. Later the user asks "where are my keys?" and the app shows where they were last seen and plays the video at that exact second.

We track movable personal items and use furniture as spatial anchors. Furniture, walls and decor are never tracked as items.

## Who owns what

One person owns each folder. **Do not edit folders you don't own.** If you need a change in someone else's folder, ask them.

| Folder | Owner | Contents |
| --- | --- | --- |
| `ai/` | A | Prompts, Gemini code (`analyze.py`, `answer.py`, `diff.py`), `eval/` |
| `backend/` | B | FastAPI server, SQLite, ffmpeg clips, seed script |
| `frontend/` | C | React app: Scan, Search, History screens |
| `docs/`, `testdata/`, `scripts/` | D | Contract, demo script, bug list, ground truth, helper scripts |
| root files (`README.md`, `AGENTS.md`, `CLAUDE.md`, `.env.example`, `.gitignore`) | D | |

Branches: `a/prompts`, `b/pipeline`, `c/search-ui`, `d/docs`. Never push straight to `main`; open a pull request and D merges it.

## API contract

The full contract is in [docs/contract.md](docs/contract.md). It is the only file everyone shares. Do not change it without telling the team first.

Endpoints: `POST /scans`, `GET /scans`, `GET /scans/{id}`, `GET /find?q=`, `GET /changes`, `GET /health`.

Every found item has exactly these fields: `label`, `description`, `anchor`, `position`, `confidence` (0 to 1), `video_seconds`.

The function A hands to B: `analyze_video(path, watchlist)` returns a list of items.

## Tools and habits

- Python 3.11 or newer, FastAPI, SQLite, ffmpeg (backend and AI).
- React with Vite (frontend). All server calls go through `frontend/src/api.js`, which switches between mock and real data.
- Gemini API for video analysis. Keep scans to 30-60 seconds.
- Run tests: `pytest` for `ai/` and `backend/`; `npm test` / `npm run lint` in `frontend/`.

## Hard rules

- Never commit `.env`, API keys, or video files.
- Write fake sample data (mock data) and tests first.
- Keep functions small.
- Pull before each session (`git pull origin main`) and commit in small steps.
- Do not let two AI tools edit the same file.
