# Yado — Yet Another Doodle

A self-hosted Doodle-like app for finding dates that work for multiple people. No accounts required.

## Features

- **No accounts** — share a link, anyone can vote
- **Calendar view** with click, shift+click (range), and drag selection
- **Quick-fill buttons** — next 7/30 days, weekdays only
- **Real-time updates** via WebSocket
- **Vote counts** on the calendar with crowns on the best date(s)
- **Admin controls** — close or delete polls via a secret admin link
- **Single-container Docker deployment** with SQLite

## Quick Start

### Pre-built image (recommended)

```bash
# Using the example compose file
curl -O https://raw.githubusercontent.com/n-gao/yado/main/docker-compose.example.yml
docker compose -f docker-compose.example.yml up -d

# Or run directly
docker run -p 8000:8000 -v yado-data:/data ghcr.io/n-gao/yado:main
```

Open [http://localhost:8000](http://localhost:8000).

### Build from source

```bash
git clone https://github.com/n-gao/yado.git
cd yado
docker compose up -d
```

### Development

```bash
# Terminal 1: backend
cd backend
uv sync
uv run uvicorn yado.main:app --reload

# Terminal 2: frontend (proxies /api to backend)
cd frontend
npm install
npm run dev
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLModel, SQLAlchemy |
| Frontend | Svelte 5, SvelteKit (SPA mode), Tailwind CSS |
| Database | SQLite (WAL mode) via aiosqlite |
| Real-time | WebSockets (FastAPI native) |
| Deployment | Docker, multi-stage build |

## Architecture

```
┌─────────────────────────────────┐
│         Docker Container        │
│                                 │
│  ┌──────────┐  ┌─────────────┐  │
│  │ uvicorn  │  │ SvelteKit   │  │
│  │(FastAPI) │  │ static build│  │
│  │          ├──┤ served by   │  │
│  │ API + WS │  │ FastAPI     │  │
│  └────┬─────┘  └─────────────┘  │
│       │                         │
│  ┌────┴─────┐                   │
│  │  SQLite  │ ← volume mount    │
│  └──────────┘                   │
└─────────────────────────────────┘
```

FastAPI serves both the REST API (`/api/*`) and the SvelteKit static build (everything else). A catch-all route serves `index.html` for SPA client-side routing.

## Project Structure

```
yado/
├── backend/
│   ├── pyproject.toml
│   ├── yado/
│   │   ├── main.py          # FastAPI app, SPA serving
│   │   ├── models.py        # SQLModel models
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── database.py      # Engine, session
│   │   └── routers/
│   │       ├── polls.py     # Poll CRUD + voting
│   │       └── ws.py        # WebSocket pub/sub
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── routes/          # SvelteKit pages
│   │   └── lib/
│   │       ├── api.ts       # API client
│   │       └── components/  # Calendar, VoteCalendar, VoteGrid
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Build from source
└── docker-compose.example.yml  # Pre-built image
```

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/polls` | Create a poll |
| GET | `/api/polls/{id}` | Get poll with votes |
| POST | `/api/polls/{id}/vote` | Submit or update a vote |
| POST | `/api/polls/{id}/close` | Close a poll (admin) |
| DELETE | `/api/polls/{id}` | Delete a poll (admin) |
| WS | `/api/polls/{id}/ws` | Real-time vote updates |

> **Note:** This project was entirely vibe coded.
