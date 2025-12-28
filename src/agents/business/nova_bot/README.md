# NovaBot

NovaBot is a demo customer support bot for Noveum, backed by the Noveum docs at `https://noveum.ai/docs`.

## Get started
See `getstarted.md`.

## How it works
- **Answer generation**: Gemini (set `GEMINI_API_KEY`)
- **Retrieval**: OpenAI embeddings over a local index (set `OPENAI_API_KEY`)
- **Index refresh**: run the scripts in `scripts/` to rebuild `NoveumDocsData/index/*`

## API
- Existing agent route:
  - `POST /agents/business.nova_bot/chat`
- Dedicated convenience route:
  - `POST /novabot/chat`

## Env vars
- `GEMINI_API_KEY` (required for answers)
- `GEMINI_MODEL` (default: `gemini-1.5-flash`)
- `OPENAI_API_KEY` (required for embeddings-based retrieval)
- `OPENAI_EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- `NOVEUM_API_KEY` (required for Noveum tracing)
- `NOVEUM_PROJECT` (default: `novabot`)
- `NOVEUM_ENVIRONMENT` (default: `development`)
- `NOVEUM_ENABLED` (default: `true`)
- `NOVABOT_DOCS_JSON_PATH` (default: `NoveumDocsData/processed/docs.json`)
- `NOVABOT_VECTORS_PATH` (default: `NoveumDocsData/index/vectors.npy`)
- `NOVABOT_INDEX_METADATA_PATH` (default: `NoveumDocsData/index/metadata.json`)


