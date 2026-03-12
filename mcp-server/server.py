"""
Sidekicks MCP Server
====================
Local MCP server that gives Claude Desktop autonomous access to:
  - Ryu 🥋    (Gemini Flash)        — fast lookups, summarization
  - Groot 🌱  (Llama-3.3-70B/Groq)  — boilerplate, Q&A, drafting
  - Talus 🗿  (Mistral Large)        — code explanation, multilingual
  - Galactus🌌(DeepSeek-V3/NVIDIA)  — deep reasoning, analysis

Transport: stdio (Claude Desktop spawns this as a subprocess)
"""

import json
import os
import asyncio
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import httpx
from mcp.server.fastmcp import FastMCP

# ── Server init ───────────────────────────────────────────────────────
mcp = FastMCP("sidekicks_mcp")

# ── Keys from environment (set in claude_desktop_config.json) ─────────
GEMINI_KEY  = os.environ.get("GEMINI_API_KEY", "")
GROQ_KEY    = os.environ.get("GROQ_API_KEY", "")
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY", "")
NVIDIA_KEY  = os.environ.get("NVIDIA_API_KEY", "")

# ── Shared HTTP error handler ─────────────────────────────────────────
def _handle_error(e: Exception, agent: str) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 401:
            return f"[{agent}] ❌ Invalid API key. Check your {agent.upper()}_API_KEY."
        if e.response.status_code == 429:
            return f"[{agent}] ❌ Rate limit hit. Wait a moment and retry."
        return f"[{agent}] ❌ HTTP {e.response.status_code}: {e.response.text[:200]}"
    if isinstance(e, httpx.TimeoutException):
        return f"[{agent}] ❌ Request timed out. Try a shorter prompt or retry."
    return f"[{agent}] ❌ Unexpected error: {type(e).__name__}: {str(e)}"

# ── Input models ──────────────────────────────────────────────────────

class SidekickInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    prompt: str = Field(..., description="The task or question to send to this sidekick.", min_length=1, max_length=8000)
    max_tokens: Optional[int] = Field(default=1024, description="Max tokens in response (1-4096).", ge=1, le=4096)
    temperature: Optional[float] = Field(default=0.3, description="Response randomness (0.0-1.0).", ge=0.0, le=1.0)

# ── Tools ─────────────────────────────────────────────────────────────

@mcp.tool(
    name="sidekick_ryu",
    annotations={"readOnlyHint": True, "destructiveHint": False,
                 "idempotentHint": False, "openWorldHint": True}
)
async def sidekick_ryu(params: SidekickInput) -> str:
    """Call Ryu 🥋 — Gemini 2.0 Flash. Best for: fast lookups, web research,
    summarization, quick questions, fact-checking. Very fast response time.

    Args:
        params (SidekickInput): prompt, max_tokens (default 1024), temperature (default 0.3)

    Returns:
        str: Ryu's response text, or an error message prefixed with [Ryu] ❌
    """
    if not GEMINI_KEY:
        return "[Ryu] ❌ GEMINI_API_KEY not set. Add it to claude_desktop_config.json env section."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": params.prompt}]}],
        "generationConfig": {
            "temperature": params.temperature,
            "maxOutputTokens": params.max_tokens
        }
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            d = r.json()
            if "error" in d:
                return f"[Ryu] ❌ {d['error']['message']}"
            return d["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return _handle_error(e, "Ryu")


@mcp.tool(
    name="sidekick_groot",
    annotations={"readOnlyHint": True, "destructiveHint": False,
                 "idempotentHint": False, "openWorldHint": True}
)
async def sidekick_groot(params: SidekickInput) -> str:
    """Call Groot 🌱 — Llama-3.3-70B via Groq. Best for: boilerplate code generation,
    drafting, Q&A, fast structured output. Extremely fast inference (~500 tokens/sec).

    Args:
        params (SidekickInput): prompt, max_tokens (default 1024), temperature (default 0.3)

    Returns:
        str: Groot's response text, or an error message prefixed with [Groot] ❌
    """
    if not GROQ_KEY:
        return "[Groot] ❌ GROQ_API_KEY not set. Add it to claude_desktop_config.json env section."

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={"model": "llama-3.3-70b-versatile",
                      "messages": [{"role": "user", "content": params.prompt}],
                      "temperature": params.temperature,
                      "max_tokens": params.max_tokens},
                headers={"Authorization": f"Bearer {GROQ_KEY}"}
            )
            r.raise_for_status()
            d = r.json()
            if "error" in d:
                return f"[Groot] ❌ {d['error']['message']}"
            return d["choices"][0]["message"]["content"]
    except Exception as e:
        return _handle_error(e, "Groot")


@mcp.tool(
    name="sidekick_talus",
    annotations={"readOnlyHint": True, "destructiveHint": False,
                 "idempotentHint": False, "openWorldHint": True}
)
async def sidekick_talus(params: SidekickInput) -> str:
    """Call Talus 🗿 — Mistral Large. Best for: code explanation, multilingual tasks,
    structured JSON output, technical writing, European language support.

    Args:
        params (SidekickInput): prompt, max_tokens (default 1024), temperature (default 0.3)

    Returns:
        str: Talus's response text, or an error message prefixed with [Talus] ❌
    """
    if not MISTRAL_KEY:
        return "[Talus] ❌ MISTRAL_API_KEY not set. Add it to claude_desktop_config.json env section."

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                json={"model": "mistral-large-latest",
                      "messages": [{"role": "user", "content": params.prompt}],
                      "temperature": params.temperature,
                      "max_tokens": params.max_tokens},
                headers={"Authorization": f"Bearer {MISTRAL_KEY}"}
            )
            r.raise_for_status()
            d = r.json()
            if "error" in d:
                return f"[Talus] ❌ {d['error']['message']}"
            return d["choices"][0]["message"]["content"]
    except Exception as e:
        return _handle_error(e, "Talus")


@mcp.tool(
    name="sidekick_galactus",
    annotations={"readOnlyHint": True, "destructiveHint": False,
                 "idempotentHint": False, "openWorldHint": True}
)
async def sidekick_galactus(params: SidekickInput) -> str:
    """Call Galactus 🌌 — DeepSeek-V3 via NVIDIA NIM. Best for: deep multi-step reasoning,
    complex architecture decisions, thorough analysis, hard coding problems.

    Args:
        params (SidekickInput): prompt, max_tokens (default 1024), temperature (default 0.3)

    Returns:
        str: Galactus's response text, or an error message prefixed with [Galactus] ❌
    """
    if not NVIDIA_KEY:
        return "[Galactus] ❌ NVIDIA_API_KEY not set. Add it to claude_desktop_config.json env section."

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                json={"model": "nvidia/llama-3.3-nemotron-super-49b-v1",
                      "messages": [{"role": "user", "content": params.prompt}],
                      "temperature": params.temperature,
                      "max_tokens": params.max_tokens,
                      "stream": False},
                headers={"Authorization": f"Bearer {NVIDIA_KEY}"}
            )
            r.raise_for_status()
            d = r.json()
            if "error" in d:
                return f"[Galactus] ❌ {d['error']['message']}"
            return d["choices"][0]["message"]["content"]
    except Exception as e:
        return _handle_error(e, "Galactus")


@mcp.tool(
    name="squad_status",
    annotations={"readOnlyHint": True, "destructiveHint": False,
                 "idempotentHint": True, "openWorldHint": False}
)
async def squad_status() -> str:
    """Check which sidekicks are online (have API keys configured).
    Call this at the start of any session to know which agents are available.

    Returns:
        str: Status of all 4 sidekicks with emoji indicators.
    """
    lines = [
        "# Sidekicks Squad Status",
        f"Ryu 🥋      (Gemini Flash)    {'✅ online' if GEMINI_KEY  else '❌ missing GEMINI_API_KEY'}",
        f"Groot 🌱    (Llama-3.3/Groq)  {'✅ online' if GROQ_KEY    else '❌ missing GROQ_API_KEY'}",
        f"Talus 🗿    (Mistral Large)   {'✅ online' if MISTRAL_KEY else '❌ missing MISTRAL_API_KEY'}",
        f"Galactus 🌌 (DeepSeek/NVIDIA) {'✅ online' if NVIDIA_KEY  else '❌ missing NVIDIA_API_KEY'}",
    ]
    return "\n".join(lines)


@mcp.tool(
    name="squad_batch",
    annotations={"readOnlyHint": True, "destructiveHint": False,
                 "idempotentHint": False, "openWorldHint": True}
)
async def squad_batch(
    prompt: str = Field(..., description="The task to send to ALL available sidekicks in parallel."),
    max_tokens: Optional[int] = Field(default=512, description="Max tokens per sidekick response.", ge=1, le=2048)
) -> str:
    """Send the same prompt to ALL available sidekicks simultaneously and return all responses.
    Use this for getting multiple perspectives, cross-checking answers, or parallel research.

    Args:
        prompt (str): Task to send to all sidekicks
        max_tokens (int): Max tokens per response (default 512 to keep it fast)

    Returns:
        str: Markdown-formatted responses from all available sidekicks.
    """
    tasks = {}
    if GEMINI_KEY:  tasks["Ryu 🥋"]      = sidekick_ryu
    if GROQ_KEY:    tasks["Groot 🌱"]    = sidekick_groot
    if MISTRAL_KEY: tasks["Talus 🗿"]    = sidekick_talus
    if NVIDIA_KEY:  tasks["Galactus 🌌"] = sidekick_galactus

    if not tasks:
        return "❌ No sidekicks online. Check your API keys in claude_desktop_config.json."

    inp = SidekickInput(prompt=prompt, max_tokens=max_tokens)
    results = await asyncio.gather(*[fn(inp) for fn in tasks.values()], return_exceptions=True)

    output = ["# Squad Batch Results\n"]
    for name, result in zip(tasks.keys(), results):
        output.append(f"## {name}")
        output.append(str(result) if not isinstance(result, Exception) else f"❌ Error: {result}")
        output.append("")

    return "\n".join(output)


# ── Entry point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()  # stdio transport — Claude Desktop spawns this
