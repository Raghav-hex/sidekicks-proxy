---
title: SideKicks
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 5.0.0
app_file: app.py
pinned: true
tags:
  - mcp-server
---

# SideKicks MCP Server 🤖

Claude's AI sidekick squad, exposed as MCP tools.

## Tools exposed via MCP
- `call_ryu(prompt)` — Gemini Flash, fast lookups
- `call_groot(prompt)` — Llama-3.3-70B via Groq, boilerplate
- `call_talus(prompt)` — Mistral Large, code/multilingual
- `call_galactus(prompt)` — DeepSeek-V3 via NVIDIA, deep reasoning
- `squad_status()` — check which agents are online

## Space Secrets needed
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `MISTRAL_API_KEY`
- `NVIDIA_API_KEY`
