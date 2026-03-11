from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
import os

app = FastAPI(title="Sidekicks Proxy", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Keys from environment ─────────────────────────────────────────────
GEMINI_KEY  = os.environ.get("GEMINI_API_KEY", "")
GROQ_KEY    = os.environ.get("GROQ_API_KEY", "")
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY", "")
NVIDIA_KEY  = os.environ.get("NVIDIA_API_KEY", "")


class DispatchRequest(BaseModel):
    agent: str
    prompt: str

class BatchRequest(BaseModel):
    tasks: dict[str, str]  # {agent: prompt}


# ── Sidekick callers (async) ──────────────────────────────────────────

async def call_ryu(prompt: str, client: httpx.AsyncClient) -> str:
    if not GEMINI_KEY:
        return "[Ryu] ❌ GEMINI_API_KEY not set"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    r = await client.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}
    }, timeout=30)
    d = r.json()
    if "error" in d: return f"[Ryu] ❌ {d['error']['message']}"
    return d["candidates"][0]["content"]["parts"][0]["text"]


async def call_groot(prompt: str, client: httpx.AsyncClient) -> str:
    if not GROQ_KEY: return "[Groot] ❌ GROQ_API_KEY not set"
    r = await client.post("https://api.groq.com/openai/v1/chat/completions",
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.3, "max_tokens": 1024},
        headers={"Authorization": f"Bearer {GROQ_KEY}"}, timeout=30)
    d = r.json()
    if "error" in d: return f"[Groot] ❌ {d['error']['message']}"
    return d["choices"][0]["message"]["content"]


async def call_talus(prompt: str, client: httpx.AsyncClient) -> str:
    if not MISTRAL_KEY: return "[Talus] ❌ MISTRAL_API_KEY not set"
    r = await client.post("https://api.mistral.ai/v1/chat/completions",
        json={"model": "mistral-large-latest",
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.3, "max_tokens": 1024},
        headers={"Authorization": f"Bearer {MISTRAL_KEY}"}, timeout=30)
    d = r.json()
    if "error" in d: return f"[Talus] ❌ {d['error']['message']}"
    return d["choices"][0]["message"]["content"]


async def call_galactus(prompt: str, client: httpx.AsyncClient) -> str:
    if not NVIDIA_KEY: return "[Galactus] ❌ NVIDIA_API_KEY not set"
    r = await client.post("https://integrate.api.nvidia.com/v1/chat/completions",
        json={"model": "deepseek-ai/deepseek-v3-0324",
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.3, "max_tokens": 1024, "stream": False},
        headers={"Authorization": f"Bearer {NVIDIA_KEY}"}, timeout=60)
    d = r.json()
    if "error" in d: return f"[Galactus] ❌ {d['error']['message']}"
    return d["choices"][0]["message"]["content"]


AGENTS = {
    "ryu":      call_ryu,
    "groot":    call_groot,
    "talus":    call_talus,
    "galactus": call_galactus,
}


# ── Routes ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Sidekicks online 🚀", "agents": list(AGENTS.keys())}


@app.get("/status")
def status():
    return {
        "ryu":      "✅ online" if GEMINI_KEY  else "❌ no key",
        "groot":    "✅ online" if GROQ_KEY    else "❌ no key",
        "talus":    "✅ online" if MISTRAL_KEY else "❌ no key",
        "galactus": "✅ online" if NVIDIA_KEY  else "❌ no key",
    }


@app.post("/dispatch")
async def dispatch(req: DispatchRequest):
    """Call a single sidekick."""
    agent = req.agent.lower().strip()
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent '{agent}'. Choose: {list(AGENTS.keys())}")
    async with httpx.AsyncClient() as client:
        result = await AGENTS[agent](req.prompt, client)
    return {"agent": agent, "response": result}


@app.post("/batch")
async def batch(req: BatchRequest):
    """Call multiple sidekicks in parallel. Returns all results at once."""
    invalid = [a for a in req.tasks if a not in AGENTS]
    if invalid:
        raise HTTPException(400, f"Unknown agents: {invalid}. Choose from: {list(AGENTS.keys())}")

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[
            AGENTS[agent](prompt, client)
            for agent, prompt in req.tasks.items()
        ])

    return {"results": dict(zip(req.tasks.keys(), results))}
