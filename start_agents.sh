#!/bin/bash
# S25 Lumiere - Agent Mesh Launcher for AlienStef
cd ~/S25-COMMAND-CENTER
source .venv/bin/activate
set -a; source .env; set +a
export MEMORY_DIR=./memory
export COCKPIT_URL=http://localhost:7777
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5-coder:14b

echo '[S25] Launching agent mesh...'

# Agent Loop (market data collector + Merlin intel)
nohup python3 -m agents.agent_loop > /tmp/s25_agent_loop.log 2>&1 &
echo $! > /tmp/s25_agent_loop.pid
echo "[S25] agent_loop PID=$!"

# Oracle Agent (price feeds)
nohup python3 -m agents.oracle_agent > /tmp/s25_oracle.log 2>&1 &
echo $! > /tmp/s25_oracle.pid
echo "[S25] oracle_agent PID=$!"

# Onchain Guardian (contract monitor)
nohup python3 -m agents.onchain_guardian > /tmp/s25_onchain.log 2>&1 &
echo $! > /tmp/s25_onchain.pid
echo "[S25] onchain_guardian PID=$!"

# Merlin Feedback Loop
nohup python3 -m agents.merlin_feedback_loop > /tmp/s25_merlin_feedback.log 2>&1 &
echo $! > /tmp/s25_merlin_feedback.pid
echo "[S25] merlin_feedback PID=$!"

# Treasury Autopilot
nohup python3 -m agents.treasury_autopilot > /tmp/s25_treasury.log 2>&1 &
echo $! > /tmp/s25_treasury.pid
echo "[S25] treasury_autopilot PID=$!"

sleep 3
echo '[S25] Agent mesh launched. Checking processes...'
for agent in agent_loop oracle onchain merlin_feedback treasury; do
  PID=$(cat /tmp/s25_${agent}.pid 2>/dev/null)
  if kill -0 $PID 2>/dev/null; then
    echo "  ✅ $agent (PID $PID) RUNNING"
  else
    echo "  ❌ $agent (PID $PID) DEAD - check /tmp/s25_${agent}.log"
  fi
done
