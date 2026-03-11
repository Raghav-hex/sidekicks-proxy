# Sidekicks Proxy

FastAPI proxy that lets Claude call AI sidekicks autonomously.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/status` | Which sidekicks have keys |
| POST | `/dispatch` | Call a single sidekick |
| POST | `/batch` | Call multiple sidekicks in parallel |

## /dispatch
```json
{"agent": "groot", "prompt": "write hello world in Python"}
```

## /batch (parallel — all fire at once)
```json
{
  "tasks": {
    "ryu": "summarize this: ...",
    "groot": "write boilerplate for: ..."
  }
}
```

## Environment Variables
Set these in Render dashboard:
- `GEMINI_API_KEY` → aistudio.google.com
- `GROQ_API_KEY` → console.groq.com
- `MISTRAL_API_KEY` → console.mistral.ai
- `NVIDIA_API_KEY` → build.nvidia.com
