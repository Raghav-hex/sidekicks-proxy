#!/bin/bash
# Sidekicks MCP Setup Script
# Run once: bash setup.sh
# Then add your API keys to claude_desktop_config.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🤖 Sidekicks MCP Setup"
echo "====================="

# Install Python deps
echo "📦 Installing dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt" --quiet

# Verify server works
echo "🔍 Verifying server syntax..."
python3 -m py_compile "$SCRIPT_DIR/server.py" && echo "✅ server.py OK"

# Detect OS for config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    CONFIG_DIR="$APPDATA/Claude"
else
    CONFIG_DIR="$HOME/.config/Claude"
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Now add this to: $CONFIG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cat << EOF
{
  "mcpServers": {
    "sidekicks": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/server.py"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-key-here",
        "GROQ_API_KEY": "your-groq-key-here",
        "MISTRAL_API_KEY": "your-mistral-key-here",
        "NVIDIA_API_KEY": "your-nvidia-key-here"
      }
    }
  }
}
EOF
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 Get free API keys:"
echo "  Groq    → https://console.groq.com"
echo "  Gemini  → https://aistudio.google.com"
echo "  Mistral → https://console.mistral.ai"
echo "  NVIDIA  → https://build.nvidia.com"
echo ""
echo "🚀 Then restart Claude Desktop and I'll have the squad!"
