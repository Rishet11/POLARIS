# POLARIS demo — run & deploy

Two processes: the FastAPI engine wrapper (`api/`) and the Next.js dashboard (`frontend/`). The Python engine in `factoring/` is unchanged; the API only exposes it.

## Run locally (for recording the Loom)

Terminal 1 — API on :8600:
```bash
cd /Users/rishetmehra/Desktop/Polaris
PYTHONPATH=".venv/lib/python3.14/site-packages:." DEMO_MODE=1 \
  .venv/bin/python -m uvicorn api.main:app --port 8600
```

Terminal 2 — frontend on :3000:
```bash
cd /Users/rishetmehra/Desktop/Polaris/frontend
npm run dev
```

Open http://localhost:3000. `frontend/.env.local` already points at `http://localhost:8600`.

`DEMO_MODE=1` forces canned message templates (no Gemini key, no network, fully reproducible). To use live LLM drafting instead, unset `DEMO_MODE` and set `GOOGLE_API_KEY`.

## Deploy (public link)

**Backend — Render** (blueprint in `render.yaml`):
1. New > Blueprint, point at this repo. It provisions `polaris-api`.
2. After the frontend deploys, set `FRONTEND_ORIGIN` on the service to the Vercel URL (e.g. `https://polaris-xxxx.vercel.app`). `DEMO_MODE=1` is already set.
3. Note the service URL, e.g. `https://polaris-api.onrender.com`.

**Frontend — Vercel:**
1. Import the repo, set root directory to `frontend`.
2. Env var `NEXT_PUBLIC_API_URL` = the Render URL above.
3. Deploy. Copy the production URL back into the Render `FRONTEND_ORIGIN`.

**Cold-start warning:** Render's free/starter tier spins down when idle; the first request after idle can take 30-50s. Before any live view, hit `https://polaris-api.onrender.com/api/health` from a terminal to warm it, or record the Loom as the primary asset.

## Demo flow (~2.5 min)

1. **Cash Application** — Run Payment Matching. 5 auto-applied / 3 review / 2 exceptions, 50% auto-match on a deliberately messy feed. Deterministic, no LLM in the money path.
2. **Review queue** — approve one, reject one; both land in the same audit trail (actor human vs system).
3. **Collections** — open the top case, Send reminder, then Retry identical send → the FSM refuses it (BLOCKED_DUPLICATE_MESSAGE, stage does not advance).
4. **Portfolio** — covenants, aging chart, Export data tape (CSV).
5. Close: only the bank feed is mocked; swap it for a real feed and the engine is unchanged.
