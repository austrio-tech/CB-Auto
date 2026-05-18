# Chatbot API System — Implementation Plan

## Overview

A REST API-based chatbot that answers questions using a local knowledge base (Markdown files). When the LLM determines it needs live database data to answer, it returns a structured "data needed" response with a reference code. The caller fetches the required data and sends it back; the system then computes and returns the final answer.

---

## Architecture

```
┌─────────────┐        ┌──────────────────────────────────────────┐
│  Client App │        │              Chatbot API                  │
│             │──(1)──▶│  POST /chat      (ask question)           │
│             │◀──(2)──│  → answer  OR  → data_needed + ref_code  │
│             │        │                                           │
│             │──(3)──▶│  POST /chat/respond  (send DB data back)  │
│             │◀──(4)──│  → final answer                           │
└─────────────┘        └──────────────────────────────────────────┘
                                       │
                          ┌────────────┴────────────┐
                          │                         │
                   ┌──────▼──────┐         ┌────────▼────────┐
                   │  K_B/*.md   │         │  OpenRouter LLM  │
                   │ (Knowledge  │         │  (free tier)     │
                   │   Base)     │         └─────────────────┘
                   └─────────────┘
```

---

## Two-Phase Response Flow

### Phase 1 — Initial Question

```
POST /chat
{
  "question": "What is the outstanding balance for account #1042?"
}
```

**LLM evaluates against knowledge base:**

- **Can answer directly** → returns answer immediately:
  ```json
  {
    "status": "answered",
    "answer": "Our return policy allows 30 days..."
  }
  ```

- **Needs DB data** → returns data request:
  ```json
  {
    "status": "data_needed",
    "ref_code": "a1b2c3d4-...",
    "data_request": {
      "description": "Account balance for account #1042",
      "fields_needed": ["account_id", "balance", "last_payment_date"]
    }
  }
  ```

### Phase 2 — Caller Provides Data

```
POST /chat/respond
{
  "ref_code": "a1b2c3d4-...",
  "data": {
    "account_id": 1042,
    "balance": 250.00,
    "last_payment_date": "2026-04-15"
  }
}
```

**System retrieves original context via ref_code, feeds data to LLM:**

```json
{
  "status": "answered",
  "answer": "Account #1042 has an outstanding balance of $250.00. The last payment was made on April 15, 2026."
}
```

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Clean async support, rich ML ecosystem |
| Framework | FastAPI | Auto-docs, async, typed request/response models |
| LLM Provider | OpenRouter (free tier) | Supports many models via one API |
| Recommended Model | `mistralai/mistral-7b-instruct` or `google/gemma-3-27b-it:free` | Free tier, good instruction following |
| Knowledge Base | `.md` files in `/K_B` folder | Simple, human-editable, no DB needed |
| Session Store | In-memory dict (TTL 30 min) | Simple; swap for Redis later if needed |
| Env Config | `python-dotenv` + `.env` file | Keeps secrets out of code |

---

## Project Structure

```
ChatBot/
├── plan.md                  ← this file
├── .env                     ← OPENROUTER_API_KEY (git-ignored)
├── .env.example             ← template for .env
├── requirements.txt
├── K_B/                     ← knowledge base markdown files
│   ├── products.md
│   ├── policies.md
│   └── ...
├── app/
│   ├── main.py              ← FastAPI app entry point
│   ├── routers/
│   │   └── chat.py          ← /chat and /chat/respond endpoints
│   ├── services/
│   │   ├── llm.py           ← OpenRouter API calls
│   │   ├── knowledge.py     ← load & index K_B/*.md files
│   │   └── session.py       ← ref_code store with TTL
│   ├── models/
│   │   └── schemas.py       ← Pydantic request/response models
│   └── config.py            ← settings loaded from .env
└── tests/
    └── test_chat.py
```

---

## Implementation Steps

### Step 1 — Project Scaffold
- Create folder structure above
- Set up `requirements.txt` with: `fastapi`, `uvicorn`, `httpx`, `python-dotenv`, `pydantic`
- Create `.env` and `.env.example` with `OPENROUTER_API_KEY`

### Step 2 — Knowledge Base Loader (`knowledge.py`)
- On startup, read all `.md` files from `/K_B`
- Concatenate into a single knowledge context string
- Prepend to every LLM system prompt
- Hot-reload support optional (re-read on each request or on a file-change event)

### Step 3 — LLM Service (`llm.py`)
- `POST https://openrouter.ai/api/v1/chat/completions` via `httpx`
- System prompt structure:
  ```
  You are a business assistant. Use the knowledge base below to answer questions.
  If you need database data to answer, respond ONLY with valid JSON:
    { "needs_data": true, "description": "...", "fields_needed": ["field1", ...] }
  Otherwise respond with plain text.

  === KNOWLEDGE BASE ===
  {knowledge_base_content}
  ```
- Parse response: if JSON with `needs_data: true` → trigger Phase 2 flow; else → return text answer

### Step 4 — Session Store (`session.py`)
- Dict keyed by `ref_code` (UUID4)
- Each entry stores: `{ question, conversation_history, data_request, expires_at }`
- TTL of 30 minutes; expired entries cleaned on access or via background task
- `create_session(question, history, data_request) → ref_code`
- `get_session(ref_code) → session | None`
- `delete_session(ref_code)`

### Step 5 — Chat Router (`chat.py`)

**`POST /chat`**
1. Receive question
2. Load knowledge base
3. Call LLM with knowledge base + question
4. If LLM returns `needs_data` → create session, return `data_needed` response
5. Else → return `answered` response

**`POST /chat/respond`**
1. Receive `ref_code` + `data`
2. Look up session by `ref_code` (404 if missing/expired)
3. Rebuild conversation: original question + data provided
4. Call LLM again with data injected into context
5. Delete session
6. Return `answered` response

### Step 6 — Pydantic Schemas (`schemas.py`)
```python
# Request models
class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None  # for multi-turn conversations

class RespondRequest(BaseModel):
    ref_code: str
    data: dict

# Response models
class AnsweredResponse(BaseModel):
    status: Literal["answered"]
    answer: str

class DataNeededResponse(BaseModel):
    status: Literal["data_needed"]
    ref_code: str
    data_request: DataRequest

class DataRequest(BaseModel):
    description: str
    fields_needed: list[str]
```

### Step 7 — Wire up FastAPI (`main.py`)
- Include chat router
- CORS middleware (allow your app origins)
- Startup event: load knowledge base into memory
- Health check: `GET /health`

### Step 8 — Testing
- Test direct-answer flow with a question answerable from K_B
- Test data-needed flow with a question requiring DB data
- Test expired ref_code returns 404
- Test invalid ref_code returns 404

---

## API Reference (Final)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/chat` | Send question, get answer or data_needed |
| `POST` | `/chat/respond` | Send DB data by ref_code, get final answer |

---

## Security Considerations

- Store `OPENROUTER_API_KEY` in `.env` only, never in code
- Add API key auth to your endpoints (simple `X-API-Key` header check) so only your apps can call them
- Validate and sanitize incoming `data` payloads in `/chat/respond`
- Set CORS to allow only your specific app origins
- Ref codes are UUID4 (non-guessable) and expire after 30 minutes

---

## OpenRouter Free Tier Notes

- Free tier has rate limits (typically ~20 req/min, varies by model)
- Models tagged `:free` are zero-cost — good starting options:
  - `mistralai/mistral-7b-instruct:free`
  - `google/gemma-3-27b-it:free`
  - `meta-llama/llama-3.1-8b-instruct:free`
- Add `HTTP-Referer` and `X-Title` headers to OpenRouter requests (required by their policy)
- Monitor usage at `openrouter.ai/activity`

---

## Future Enhancements (Not in Scope Now)

- Redis for session store (multi-instance deployment)
- Vector embeddings for semantic KB search (when KB grows large)
- Conversation history / multi-turn chat sessions
- Streaming responses via SSE
- Admin endpoint to reload knowledge base without restart
