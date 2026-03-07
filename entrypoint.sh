#!/bin/sh
# ============================================================
# S25 LUMIÈRE — Multi-Service Entrypoint
# Une seule image Docker → 5 services selon SERVICE= env var
# ============================================================
set -e

SERVICE="${SERVICE:-core-dev}"
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   S25 LUMIÈRE — Service: $SERVICE"
echo "╚══════════════════════════════════════╝"
echo ""

case "$SERVICE" in

  "core-dev")
    echo "🚀 Starting Core-Dev Cockpit (port ${PORT:-7777})..."
    exec python agents/cockpit_lumiere.py
    ;;

  "intel-comet")
    echo "🟣 Starting Intel-COMET Bridge (port ${PORT:-7778})..."
    exec python agents/comet_bridge.py --server --port "${PORT:-7778}"
    ;;

  "voice-relay")
    echo "🎙️  Starting Voice Relay WebSocket (port ${PORT:-7779})..."
    exec python agents/s25_voice_relay.py
    ;;

  "executor")
    echo "⚡ Starting Executor — ARKON-5 + Treasury (port ${PORT:-7780})..."
    exec python scripts/arkon5_bridge.py --watch --port "${PORT:-7780}"
    ;;

  "monitor")
    echo "📊 Starting Monitor — Watchdog (port ${PORT:-7781})..."
    exec python scripts/monitor_service.py --port "${PORT:-7781}"
    ;;

  "all")
    echo "🔥 Starting ALL services (dev mode)..."
    python agents/cockpit_lumiere.py &
    python agents/s25_voice_relay.py &
    python scripts/arkon5_bridge.py --watch &
    wait
    ;;

  *)
    echo "❌ SERVICE inconnu: $SERVICE"
    echo "   Options: core-dev, intel-comet, voice-relay, executor, monitor, all"
    exit 1
    ;;

esac
