# S25 SHARED MEMORY — bras-alien v0.3.0

> Last updated: 2026-04-11 (session 3)

## Architecture

- **AlienStef** (10.0.0.97) — Alienware Aurora R4, Ubuntu 24.04
- **Dell-Linux** (10.0.0.202) — Dell standby node, llama3
- **Doctrine**: git.smajor + HA + Alien + Cloudflare

### Services (docker-compose.fullstack.yml)

| Service | Container | Port | Status |
|---------|-----------|------|--------|
| bras-alien router | s25-bras-alien | 8787 | UP |
| Open WebUI | s25-open-webui | 3000 | UP |
| OpenJarvis | s25-openjarvis | 3002 | UP (fixed session 3) |
| Ollama (host) | — | 11434 | UP |

### Router Fleet (port 8787)

- **bras-alien** (primary): qwen2.5-coder:7b @ 10.0.0.97:11434 — 3ms probe
- **dell-linux-llama3** (standby): llama3:latest @ 10.0.0.202:11434 — 55ms probe

### Cloud Providers (OpenRouter)

Free tier:
- meta-llama/llama-3.3-70b-instruct:free
- qwen/qwen3-coder:free
- google/gemma-4-31b-it:free
- nousresearch/hermes-3-llama-3.1-405b:free
- openai/gpt-oss-120b:free

### Agent Personas (Open WebUI)

| Persona | Role | Backend Model | Status |
|---------|------|---------------|--------|
| ARKON | Agent Principal | arkon-auto (local first) | OK |
| TRINITY | Intel & Strategie | arkon-free (cloud first) | BLOCKED (OpenRouter spend limit) |
| MERLIN | Deep Research | arkon-free (gemma-4-31b) | OK |

### Virtual Models

- `arkon-auto` — local > free > paid
- `arkon-local` — local only
- `arkon-free` — free cloud > local > paid
- `arkon-paid` — paid > free > local

## API Keys

- **OPENROUTER_API_KEY**: set in .env (sk-or-v1-...)
- **OPENJARVIS_API_KEY**: s25-jarvis-internal-key
- **OPENAI_API_KEY**: bras-alien-internal (for OpenJarvis -> router)
- **KIMI_API_KEY**: not configured (sk-REPLACE-ME)

## Fixes Applied (session 2+3)

### Fix 1 — SSE Streaming (session 2)
Router `/v1/chat/completions` now supports `stream: true` via fake SSE wrapper.

### Fix 2 — uv sync (session 2)
Added `--extra server` to `uv sync` in Dockerfile.bras-alien.

### Fix 3 — OPENJARVIS_API_KEY (session 2)
Added to openjarvis docker-compose environment.

### Fix 4 — Cloud providers (session 2)
Updated to 5 verified free OpenRouter models.

### Fix 5 — OpenJarvis EngineConnectionError (session 3)
**Root cause**: OpenJarvis uses the standard OpenAI Python client which requires `OPENAI_API_KEY` and `OPENAI_BASE_URL` env vars. Only `BRAS_ALIEN_URL` was set (used by entrypoint for config.toml patching but NOT by the OpenAI client).
**Fix**: Added `OPENAI_API_KEY: "bras-alien-internal"` and `OPENAI_BASE_URL: "http://bras-alien:8787/v1"` to docker-compose openjarvis service.
**Commit**: fix(openjarvis): add OPENAI_API_KEY + OPENAI_BASE_URL env vars

## Known Issues

1. **TRINITY timeout**: OpenRouter spend limit at $0. Stef needs to increase on openrouter.ai dashboard.
2. **OpenJarvis SSE streaming**: `stream: true` hangs (never terminates). Non-streaming works fine.
3. **OpenJarvis /v1/models**: Returns empty list. Chat completions work regardless.

## Next Steps

- [ ] Fix OpenRouter spend limit for TRINITY
- [ ] Stability test 48h
- [ ] Akash deployment
- [ ] OpenJarvis agent features (deep_research, monitor, morning_digest)
