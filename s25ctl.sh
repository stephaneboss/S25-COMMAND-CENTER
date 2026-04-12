#!/bin/bash
# ════════════════════════════════════════════
# S25 LUMIÈRE — Control Script
# ════════════════════════════════════════════
S25_HOME="$HOME/S25-COMMAND-CENTER"
PIDFILE="/tmp/s25_cockpit.pid"
LOGFILE="/tmp/s25_cockpit.log"

start() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
        echo "[S25] Cockpit already running (PID $(cat $PIDFILE))"
        return 0
    fi
    echo "[S25] Starting cockpit..."
    cd "$S25_HOME"
    source .venv/bin/activate
    set -a; source .env; set +a
    export MEMORY_DIR=./memory
    export OLLAMA_URL=http://localhost:11434
    export OLLAMA_MODEL=qwen2.5-coder:14b
    export PORT=7777
    nohup python3 cockpit_lumiere.py >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    disown
    sleep 2
    if curl -s -o /dev/null -w '' http://localhost:7777/; then
        echo "[S25] ⚡ Cockpit UP on :7777 (PID $(cat $PIDFILE))"
    else
        echo "[S25] WARNING: Cockpit may not have started correctly"
        tail -5 "$LOGFILE"
    fi
}

stop() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo "[S25] Cockpit stopped (PID $PID)"
        fi
        rm -f "$PIDFILE"
    fi
    # Kill any stragglers
    pkill -f "python3 cockpit_lumiere.py" 2>/dev/null
}

restart() {
    stop
    sleep 1
    start
}

status() {
    echo "═══ S25 LUMIÈRE STATUS ═══"
    if systemctl --user is-active s25-cockpit.service &>/dev/null; then
        PID=$(systemctl --user show s25-cockpit.service -p MainPID --value)
        echo "Cockpit: RUNNING (PID $PID, systemd)"
    elif [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
        echo "Cockpit: RUNNING (PID $(cat $PIDFILE), manual)"
    else
        echo "Cockpit: DOWN"
    fi
    echo ""
    echo "─── Services ───"
    docker ps --format "  {{.Names}}: {{.Status}}" 2>/dev/null
    echo ""
    echo "─── Ollama ───"
    curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "import sys,json; [print(f'  {m[\"name\"]}') for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null || echo "  DOWN"
    echo ""
    echo "─── GPU ───"
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null | sed 's/^/  /'
    echo ""
    echo "─── Mesh ───"
    curl -s http://localhost:7777/api/mesh/status 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin).get('mesh',{})
print(f'  Agents: {d.get(\"total_agents\",0)} total, {d.get(\"online\",0)} online, {d.get(\"offline\",0)} offline')
" 2>/dev/null || echo "  Mesh unavailable"
    echo ""
    echo "─── Disk/RAM ───"
    df -h / | tail -1 | awk '{print "  Disk: "$3" / "$2" ("$5" used)"}'
    free -h | grep Mem | awk '{print "  RAM: "$3" / "$2" used, "$7" available"}'
}

agents() {
    echo "═══ AGENT MESH ═══"
    curl -s http://localhost:7777/api/mesh/status | python3 -c "
import sys,json
mesh=json.load(sys.stdin).get('mesh',{}).get('agents',{})
for name,info in sorted(mesh.items()):
    s=info.get('status','?')
    icon='●' if s=='online' else '○'
    print(f'  {icon} {name:20s} {s:10s} last_seen: {info.get(\"last_seen\",\"never\")[:19]}')
" 2>/dev/null
}

case "${1:-status}" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    agents)  agents ;;
    logs)    tail -f "$LOGFILE" ;;
    *)       echo "Usage: s25ctl {start|stop|restart|status|agents|logs}" ;;
esac
