"""
SideKicks — Gradio MCP Server
Exposes Ryu/Groot/Talus/Galactus as MCP-callable tools.
Claude calls this via dynamic_space invoke from any session.
"""

import gradio as gr
import httpx
import asyncio
import os

GEMINI_KEY  = os.environ.get("GEMINI_API_KEY", "")
GROQ_KEY    = os.environ.get("GROQ_API_KEY", "")
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY", "")
NVIDIA_KEY  = os.environ.get("NVIDIA_API_KEY", "")


# ── Sidekick callers ──────────────────────────────────────────────────

def call_ryu(prompt: str) -> str:
    """Ryu (Gemini Flash) — fast lookups, summarization, research."""
    if not GEMINI_KEY: return "[Ryu offline — GEMINI_API_KEY not set]"
    import urllib.request, json
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    if "error" in d: return f"[Ryu error: {d['error']['message']}]"
    return d["candidates"][0]["content"]["parts"][0]["text"]


def call_groot(prompt: str) -> str:
    """Groot (Llama-3.3-70B via Groq) — blazing fast boilerplate, Q&A, drafting."""
    if not GROQ_KEY: return "[Groot offline — GROQ_API_KEY not set]"
    import urllib.request, json
    body = json.dumps({"model": "llama-3.3-70b-versatile",
                       "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.3, "max_tokens": 1024}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
                                  data=body, headers={"Content-Type": "application/json",
                                                      "Authorization": f"Bearer {GROQ_KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    if "error" in d: return f"[Groot error: {d['error']['message']}]"
    return d["choices"][0]["message"]["content"]


def call_talus(prompt: str) -> str:
    """Talus (Mistral Large) — code explanation, multilingual, structured output."""
    if not MISTRAL_KEY: return "[Talus offline — MISTRAL_API_KEY not set]"
    import urllib.request, json
    body = json.dumps({"model": "mistral-large-latest",
                       "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.3, "max_tokens": 1024}).encode()
    req = urllib.request.Request("https://api.mistral.ai/v1/chat/completions",
                                  data=body, headers={"Content-Type": "application/json",
                                                      "Authorization": f"Bearer {MISTRAL_KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    if "error" in d: return f"[Talus error: {d['error']['message']}]"
    return d["choices"][0]["message"]["content"]


def call_galactus(prompt: str) -> str:
    """Galactus (DeepSeek-V3 via NVIDIA NIM) — deep reasoning, complex analysis."""
    if not NVIDIA_KEY: return "[Galactus offline — NVIDIA_API_KEY not set]"
    import urllib.request, json
    body = json.dumps({"model": "deepseek-ai/deepseek-v3-0324",
                       "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.3, "max_tokens": 1024, "stream": False}).encode()
    req = urllib.request.Request("https://integrate.api.nvidia.com/v1/chat/completions",
                                  data=body, headers={"Content-Type": "application/json",
                                                      "Authorization": f"Bearer {NVIDIA_KEY}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    if "error" in d: return f"[Galactus error: {d['error']['message']}]"
    return d["choices"][0]["message"]["content"]


def squad_status() -> str:
    """Check which sidekicks are online."""
    return "\n".join([
        f"Ryu 🥋      {'✅ online' if GEMINI_KEY  else '❌ no GEMINI_API_KEY'}",
        f"Groot 🌱    {'✅ online' if GROQ_KEY    else '❌ no GROQ_API_KEY'}",
        f"Talus 🗿    {'✅ online' if MISTRAL_KEY else '❌ no MISTRAL_API_KEY'}",
        f"Galactus 🌌 {'✅ online' if NVIDIA_KEY  else '❌ no NVIDIA_API_KEY'}",
    ])


# ── Gradio MCP Interface ──────────────────────────────────────────────

with gr.Blocks(title="SideKicks MCP") as demo:
    gr.Markdown("# SideKicks 🤖\nClaude's AI sidekick squad — callable via MCP")

    with gr.Tab("Status"):
        status_out = gr.Textbox(label="Squad Status", lines=4)
        gr.Button("Check Status").click(squad_status, outputs=status_out)

    with gr.Tab("Ryu 🥋"):
        ryu_in  = gr.Textbox(label="Prompt", lines=3)
        ryu_out = gr.Textbox(label="Response", lines=8)
        gr.Button("Ask Ryu").click(call_ryu, inputs=ryu_in, outputs=ryu_out)

    with gr.Tab("Groot 🌱"):
        groot_in  = gr.Textbox(label="Prompt", lines=3)
        groot_out = gr.Textbox(label="Response", lines=8)
        gr.Button("Ask Groot").click(call_groot, inputs=groot_in, outputs=groot_out)

    with gr.Tab("Talus 🗿"):
        talus_in  = gr.Textbox(label="Prompt", lines=3)
        talus_out = gr.Textbox(label="Response", lines=8)
        gr.Button("Ask Talus").click(call_talus, inputs=talus_in, outputs=talus_out)

    with gr.Tab("Galactus 🌌"):
        gal_in  = gr.Textbox(label="Prompt", lines=3)
        gal_out = gr.Textbox(label="Response", lines=8)
        gr.Button("Ask Galactus").click(call_galactus, inputs=gal_in, outputs=gal_out)


# Launch with MCP server enabled — THIS is what lets Claude invoke via dynamic_space
demo.launch(mcp_server=True)
