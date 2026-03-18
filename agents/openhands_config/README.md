# OpenHands Integration — S25 Lumière

OpenHands (CodeActAgent) runs on **AlienStef** (10.0.0.97:3001) with a local RTX 3060 and `qwen2.5-coder:14b` via Ollama.

It acts as an autonomous coding agent in the S25 pipeline — reviewing code, fixing bugs, and committing changes without manual intervention.

---

## Files in this directory

| File | Purpose |
|------|---------|
| `mission_runner.sh` | CLI script to submit a task and poll for completion |
| `openhands_bridge.py` | Flask bridge (port 9292) — HTTP API for task submission |
| `tasks/smajor_daily_task.md` | Daily maintenance task for smajor.org Next.js app |
| `tasks/s25_daily_task.md` | Daily check for S25 Python agents |
| `task_history.json` | Auto-generated: persisted task history |

---

## How to submit a task

### Option 1 — CLI (mission_runner.sh)

```bash
# Default task (smajor.org review)
bash agents/openhands_config/mission_runner.sh

# Custom task
bash agents/openhands_config/mission_runner.sh "Fix the TypeScript error in dashboard.tsx"
```

Logs are written to `/tmp/openhands_mission.log`.

### Option 2 — Bridge API (openhands_bridge.py)

Start the bridge:
```bash
cd /path/to/repo
python agents/openhands_config/openhands_bridge.py
# Listening on http://0.0.0.0:9292
```

Submit a task:
```bash
curl -X POST http://localhost:9292/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Review smajor-command-center and fix TypeScript errors",
    "source": "agent_loop",
    "priority": "normal"
  }'
```

Check status:
```bash
curl http://localhost:9292/status
```

List recent tasks:
```bash
curl http://localhost:9292/tasks?limit=10
```

### Option 3 — From agent_loop.py

```python
import requests

def submit_openhands_task(task: str, source: str = "agent_loop"):
    resp = requests.post(
        "http://localhost:9292/task",
        json={"task": task, "source": source},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()  # {"bridge_id": "...", "openhands_id": "...", "status": "submitted"}
```

---

## How to check status

```bash
# Bridge health + last task
curl http://localhost:9292/status | jq .

# Task history
curl http://localhost:9292/tasks | jq '.tasks[0]'

# OpenHands UI (visual)
open http://10.0.0.97:3001
```

---

## Integration with Home Assistant

### shell_command in configuration.yaml

```yaml
shell_command:
  trigger_openhands_smajor: >
    curl -sf -X POST http://10.0.0.202:9292/task
    -H "Content-Type: application/json"
    -d '{"task": "Daily smajor.org maintenance check", "source": "ha_automation"}'
  trigger_openhands_s25: >
    curl -sf -X POST http://10.0.0.202:9292/task
    -H "Content-Type: application/json"
    -d '{"task": "Daily S25 pipeline check — lint, TODO hunt, syntax verify", "source": "ha_automation"}'
```

### Automation example

```yaml
automation:
  - alias: "OpenHands Daily smajor maintenance"
    trigger:
      - platform: time
        at: "03:00:00"
    action:
      - service: shell_command.trigger_openhands_smajor
```

---

## Daily automation setup

### cron on DELL-LINUX

```bash
# Edit crontab
crontab -e

# Add these lines:
# 3:00 AM — smajor.org check
0 3 * * * cd /path/to/s25-repo && python agents/openhands_config/openhands_bridge.py --task "$(cat agents/openhands_config/tasks/smajor_daily_task.md)" 2>/tmp/openhands_smajor.log

# 4:00 AM — S25 pipeline check
0 4 * * * cd /path/to/s25-repo && bash agents/openhands_config/mission_runner.sh "$(cat agents/openhands_config/tasks/s25_daily_task.md)" 2>/tmp/openhands_s25.log
```

Or use the bridge's `/task` endpoint from any cron:
```bash
# Simple cron via curl (bridge must be running)
0 3 * * * curl -sf -X POST http://localhost:9292/task -H "Content-Type: application/json" -d @/path/to/s25-repo/agents/openhands_config/tasks/smajor_daily_task.md
```

---

## Architecture diagram

```
HA Automation / agent_loop.py / cron
        |
        v
  openhands_bridge.py (port 9292)
        |
        v
  OpenHands API (http://10.0.0.97:3001)
        |
        v
  CodeActAgent + qwen2.5-coder:14b (Ollama local)
        |
        v
  Git repo — commits fixes, reports
        |
        v
  GitHub / smajor.org deployment
```

---

## Troubleshooting

### OpenHands not reachable

```bash
# Check from DELL-LINUX or another machine
curl http://10.0.0.97:3001/
curl http://10.0.0.97:3001/api/options/models

# Check if it's running on AlienStef
ssh user@10.0.0.97 "docker ps | grep openhands"
```

### Bridge not starting

```bash
pip install flask requests
python agents/openhands_config/openhands_bridge.py
```

### Task stuck in "submitted"

Check OpenHands UI at http://10.0.0.97:3001 — the task may be waiting for Ollama.
Ollama must be running: `curl http://10.0.0.97:11434/api/tags`

---

## Notes

- The bridge is stateless between restarts except for `task_history.json`
- OpenHands API version may vary — the bridge tries both `/api/conversations` (v0.14+) and `/api/tasks` (older)
- Tasks run with full file system access inside OpenHands container — make sure repo is mounted
- Default timeout: 10 minutes per task
