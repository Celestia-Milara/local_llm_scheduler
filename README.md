# Local LLM Privacy Scheduler

中文说明：[`README_CN.md`](README_CN.md)

A privacy-first scheduling system powered by a **local** LLM and a **skill/tool** framework.

- **Local inference**: designed to run with Ollama (no cloud LLM by default)
- **Conflict-first workflow**: detects time/travel conflicts and asks for explicit confirmation before saving
- **Encrypted sensitive fields**: schedule `title` / `description` are encrypted before persisting
- **Web UI**: Vue 3 frontend with streaming chat

## Repository layout

- `privacy_schedule_agent/` — backend (FastAPI)
- `privacy_schedule_agent/frontend/` — frontend (Vue 3)

## Prerequisites

- Python 3.10+ (recommended: 3.11+)
- Node.js 18+
- Ollama installed and running

## Quick start (local)

### 1) Start the backend

```bash
cd privacy_schedule_agent
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Backend default URL:

- `http://localhost:8000`

### 2) Start the frontend

```bash
cd privacy_schedule_agent/frontend
npm install
npm run dev
```

## Configuration

This project supports a local single-user mode and an optional cloud/multi-user mode.

### Local mode (default)

No auth middleware is enabled by default.

### Cloud mode (optional)

Set the following environment variables (for example in `privacy_schedule_agent/.env`, which is **ignored by git**):

```env
DEPLOY_MODE=cloud
JWT_SECRET=change-me-to-a-random-string
# Optional: app-layer encryption key (Fernet)
ENCRYPTION_KEY=
```

## Data & privacy notes

- SQLite database file: `privacy_schedule_agent/data/schedule.db` (ignored by git)
- Do **not** commit secrets: `.env`, tokens, private keys, or database files

## License

TBD
