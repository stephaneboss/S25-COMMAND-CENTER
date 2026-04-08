#!/bin/bash
# ================================================================
# S25 NEXUS v2.0 — ACTIVATION IMMÉDIATE sur Dell AlienStef
# Run: bash ACTIVATE_NEXUS_NOW.sh
# ================================================================
set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║   S25 NEXUS v2.0 — ACTIVATION EN COURS...           ║"
echo "╚══════════════════════════════════════════════════════╝"

# Login to GHCR (GitHub Container Registry)
echo "[1/4] Login GHCR..."
echo "$CR_PAT" | docker login ghcr.io -u stephaneboss --password-stdin 2>/dev/null || \
  docker login ghcr.io -u stephaneboss 2>/dev/null || \
  echo "⚠️  Login GHCR requis si image privée"

# Pull la nouvelle image
echo "[2/4] Pull nouvelle image S25 NEXUS v2.0..."
docker pull ghcr.io/stephaneboss/s25-command-center:main

# Redémarrer le container
echo "[3/4] Redémarrage container S25..."
if docker compose ps 2>/dev/null | grep -q s25-cockpit; then
  docker compose pull s25-cockpit
  docker compose up -d s25-cockpit
elif docker-compose ps 2>/dev/null | grep -q s25-cockpit; then
  docker-compose pull s25-cockpit
  docker-compose up -d s25-cockpit
else
  # Fallback: restart by name
  CONTAINER=$(docker ps --filter "name=s25" --format "{{.Names}}" | head -1)
  if [ -n "$CONTAINER" ]; then
    docker stop "$CONTAINER"
    docker rm "$CONTAINER"
    docker compose -f docker-compose.fallback.yml up -d
  else
    echo "⚠️  Container S25 non trouvé — démarrage depuis fallback..."
    docker compose -f docker-compose.fallback.yml up -d
  fi
fi

echo "[4/4] Vérification..."
sleep 5
curl -s http://localhost:7777/api/version | python3 -m json.tool 2>/dev/null || \
  curl -s http://localhost:7777/health 2>/dev/null || \
  echo "⚠️  Port 7777 non accessible (vérifie après 30s)"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ S25 NEXUS v2.0 ACTIVÉ!                         ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║   🌐 https://s25.smajor.org/nexus                   ║"
echo "║   📡 https://s25.smajor.org/api/v2/status           ║"
echo "║   🔐 Auth: X-S25-Secret header requis               ║"
echo "╚══════════════════════════════════════════════════════╝"
