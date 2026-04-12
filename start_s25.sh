#!/bin/bash
# S25 Lumiere — Production Launch Script (AlienStef)
cd ~/S25-COMMAND-CENTER
source .venv/bin/activate

export MEMORY_DIR=./memory
export PORT=7777

# Load .env
set -a
source .env
set +a

# Override for local
export MEMORY_DIR=./memory
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5-coder:14b

echo "[S25] Starting cockpit on port $PORT..."
exec python3 cockpit_lumiere.py
