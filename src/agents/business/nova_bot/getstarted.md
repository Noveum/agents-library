# NovaBot — Get Started

NovaBot is a demo customer support bot for Noveum docs:
- Docs source: `https://noveum.ai/docs`
- LangChain tracing reference: `https://noveum.ai/en/docs/integration-examples/langchain/overview`

It runs **via API** (FastAPI), with:
- **Answer generation**: Gemini
- **Retrieval**: OpenAI embeddings + local vector index (optional; otherwise lexical fallback)
- **Tracing**: Noveum Trace via **LangChain callback handler**

## 1) Setup a venv + install dependencies

From repo root:

```bash
cd /Users/mramanindia/work/agents-library

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip

python3 -m pip install -r src/api/requirements.txt
python3 -m pip install -r src/agents/business/nova_bot/requirements.txt
```

## 2) Configure env vars (do not hardcode secrets)

### Gemini (required)
```bash
export GEMINI_API_KEY="YOUR_GEMINI_KEY"
export GEMINI_MODEL="gemini-1.5-flash"
```

### OpenAI embeddings (recommended for better retrieval)
```bash
export OPENAI_API_KEY="YOUR_OPENAI_KEY"
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
```

### Noveum tracing (optional, but recommended)
NovaBot uses the LangChain callback approach described in Noveum’s LangChain integration docs:
`https://noveum.ai/en/docs/integration-examples/langchain/overview`

```bash
export NOVEUM_ENABLED="true"
export NOVEUM_API_KEY="YOUR_NOVEUM_KEY"
export NOVEUM_PROJECT="novabot"
export NOVEUM_ENVIRONMENT="development"
```

## 3) (Optional) Build / refresh the local embeddings index

This creates:
- `NoveumDocsData/index/vectors.npy`
- `NoveumDocsData/index/metadata.json`

```bash
python3 scripts/novabot_build_index.py
```

If you want to refresh the docs JSON first:

```bash
python3 scripts/novabot_scrape_docs.py --start-url "https://noveum.ai/docs" --max-pages 50
python3 scripts/novabot_build_index.py
```

## 4) Run the API server

```bash
python3 -m src.api.main --host 0.0.0.0 --port 8000
```

Open Swagger:
- `http://localhost:8000/docs`

## 5) Chat with NovaBot

### Option A — Dedicated route
```bash
curl -s -X POST "http://localhost:8000/novabot/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I integrate Noveum Trace with LangChain?","user_id":"demo","metadata":{"session_id":"demo-session-1"}}'
```

### Option B — Agent route
```bash
curl -s -X POST "http://localhost:8000/agents/business.nova_bot/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"What are traces and spans in Noveum?","user_id":"demo","metadata":{"session_id":"demo-session-1"}}'
```

## Notes / Troubleshooting
- **No vectors built?** NovaBot will fall back to lexical search automatically.
- **No Noveum key?** Tracing is skipped; the bot still works.
- **Missing LangChain deps?** NovaBot will still answer (Gemini SDK fallback), but you won’t get LangChain/Noveum traces.
- **Session memory (in-memory only)**: Pass `metadata.session_id` to keep chat history across requests. To clear: send `metadata.reset_session=true`.


