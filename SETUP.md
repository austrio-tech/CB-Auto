# Setup Guide

## 1. Fill in `.env`

Copy the values from `.env.example` and update these two lines in `.env`:

| Variable | What to put |
|---|---|
| `OPENROUTER_API_KEY` | Your key from https://openrouter.ai/keys |
| `API_KEY` | Any strong secret string (e.g. `my$ecretKey99`) — your client apps must send this as the `X-API-Key` header on every request |

Optionally change:

| Variable | Default | Notes |
|---|---|---|
| `OPENROUTER_MODEL` | `mistralai/mistral-7b-instruct:free` | Any `:free` model on OpenRouter works |
| `SESSION_TTL_MINUTES` | `30` | How long a `ref_code` stays valid |
| `ALLOWED_ORIGINS` | `*` | Comma-separated origins for CORS, e.g. `https://myapp.com` |

---

## 2. Add Your Knowledge Base (`K_B/`)

Drop `.md` files into the `K_B/` folder. All files are loaded at startup and injected into every LLM prompt.

- Delete `K_B/example.md` and replace with your own files.
- Suggested files: `products.md`, `policies.md`, `faq.md`, `pricing.md`
- No special format required — plain Markdown headings and paragraphs work best.
- **Reload:** restart the server after editing KB files (no hot-reload by default).

---

## 3. Install & Run Locally

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

---

## 4. Run Tests

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 5. Calling the API from Your App

**Step 1 — Ask a question:**
```http
POST /chat
X-API-Key: your_api_key_here
Content-Type: application/json

{ "question": "What is my account balance for account 1042?" }
```

**If answered directly:**
```json
{ "status": "answered", "answer": "Our return policy is 30 days..." }
```

**If DB data is needed:**
```json
{
  "status": "data_needed",
  "ref_code": "a1b2c3d4-...",
  "data_request": {
    "description": "Account balance for account #1042",
    "fields_needed": ["balance", "due_date"]
  }
}
```

**Step 2 — Query your DB, then send data back:**
```http
POST /chat/respond
X-API-Key: your_api_key_here
Content-Type: application/json

{
  "ref_code": "a1b2c3d4-...",
  "data": { "balance": 250.00, "due_date": "2026-06-01" }
}
```

**Final answer:**
```json
{ "status": "answered", "answer": "Account #1042 has a balance of $250.00 due on June 1, 2026." }
```

---

## 6. Deployment

### Option A — Any VPS / Cloud VM (recommended for simplicity)

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use **nginx** as a reverse proxy and **systemd** or **pm2** to keep the process alive.

### Option B — Railway / Render / Fly.io (zero-config PaaS)

Add a `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set your `.env` variables as environment variables in the platform dashboard (never commit `.env`).

### Option C — Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t chatbot .
docker run -p 8000:8000 --env-file .env chatbot
```

---

## Notes

- **Session expiry:** `ref_code` values expire after `SESSION_TTL_MINUTES`. If your app takes longer than that to query the DB and respond, increase this value.
- **Free tier rate limits:** OpenRouter free models allow roughly 20 requests/min. Add retry logic in your client if you hit 429 errors.
- **Scaling:** The in-memory session store is per-process. If you run multiple server instances, replace `app/services/session.py` with a Redis-backed store.
