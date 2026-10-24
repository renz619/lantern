# Lantern

HackTX '26 project. An app that remembers where you put your stuff.

1. Film a slow spin around your room with your phone.
2. Gemini watches the video and lists the small movable items it sees and where they are.
3. The app saves the list with the date and time.
4. Later, ask "where are my keys?" and the app tells you where they were last seen and plays the video at that moment.

We track movable personal items and use furniture as spatial anchors.

## Run it

Needs Python 3.11+, Node 20+, and ffmpeg.

1. Clone the repo and `cd lantern`.
2. Copy `.env.example` to `.env` and put your own Gemini API key in it. Never commit `.env`.
3. Backend: `cd backend`, create a virtualenv, `pip install -r requirements.txt`.
4. Start the server: `uvicorn app.main:app --reload`.
5. Check it: open `http://localhost:8000/health`.
6. Frontend: `cd frontend`, `npm install`, `npm run dev`.
7. Open the URL Vite prints. To use it from a phone, open an HTTPS tunnel to the backend and frontend.
8. Optional: `python backend/scripts/seed_demo.py` fills the database with sample data for the demo.

> Steps 3-4 and 8 depend on files B has not added yet. B: keep this list under 10 steps as the backend lands.

## Layout

| Folder | Owner | What |
| --- | --- | --- |
| `ai/` | A | Prompts and Gemini code |
| `backend/` | B | FastAPI server |
| `frontend/` | C | React app |
| `docs/` | D | Contract, demo script, bugs, Devpost draft |
| `testdata/` | D | Ground truth for test videos |

See [docs/contract.md](docs/contract.md) for the API contract and [AGENTS.md](AGENTS.md) for project rules.

## Privacy

A room video is private. Processing and saving stay on our own backend, and users can delete scans.
