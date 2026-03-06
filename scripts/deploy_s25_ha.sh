#!/bin/bash
# ============================================================
# S25 LUMIÈRE — Script déploiement HA complet
# Exécuter depuis SSH add-on HA:
#   bash /config/scripts/deploy_s25_ha.sh
# ============================================================

set -e
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[S25]${NC} $1"; }
ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
err() { echo -e "${RED}[ERR]${NC} $1"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $1"; }

log "⚡ S25 LUMIÈRE — Déploiement ARKON-5"
log "======================================"

# ─────────────────────────────────────────
# 1. VÉRIFICATION STRUCTURE DIRS
# ─────────────────────────────────────────
log "1. Vérification répertoires..."
mkdir -p /config/python_scripts
mkdir -p /config/scripts
mkdir -p /config/www
ok "Répertoires OK"

# ─────────────────────────────────────────
# 2. DÉPLOIEMENT ai_router.py
# ─────────────────────────────────────────
log "2. Déploiement ai_router.py v2..."
# Le fichier doit être téléchargé depuis Google Drive ou copié
if [ -f /tmp/ai_router_v2.py ]; then
    cp /tmp/ai_router_v2.py /config/python_scripts/ai_router.py
    ok "ai_router.py déployé"
else
    warn "ai_router_v2.py non trouvé dans /tmp — upload manuel requis"
fi

# ─────────────────────────────────────────
# 3. SENSORS S25 — sensors.yaml
# ─────────────────────────────────────────
log "3. Ajout sensors S25 ARKON-5..."
SENSORS_FILE="/config/sensors.yaml"

# Vérifier si les sensors S25 existent déjà
if grep -q "s25_arkon5_action" "$SENSORS_FILE" 2>/dev/null; then
    warn "Sensors S25 déjà présents dans $SENSORS_FILE"
else
    cat >> "$SENSORS_FILE" << 'EOF'

# ─────────────────────────────────────────────────────
# S25 LUMIÈRE — Sensors ARKON-5 (auto-déployé)
# ─────────────────────────────────────────────────────
- platform: rest
  name: "S25 ARKON5 Action"
  unique_id: s25_arkon5_action
  resource: "http://homeassistant.local:8123/local/ai_analysis.json"
  method: GET
  value_template: "{{ value_json.decision.action | default('HOLD') }}"
  json_attributes:
    - decision
    - timestamp
    - signal
    - execution
  scan_interval: 30
  timeout: 10

- platform: rest
  name: "S25 ARKON5 Confidence"
  unique_id: s25_arkon5_conf
  resource: "http://homeassistant.local:8123/local/ai_analysis.json"
  method: GET
  value_template: "{{ (value_json.decision.conf | default(0) * 100) | round(1) }}"
  unit_of_measurement: "%"
  scan_interval: 30
  timeout: 10

- platform: rest
  name: "S25 ARKON5 TP"
  unique_id: s25_arkon5_tp
  resource: "http://homeassistant.local:8123/local/ai_analysis.json"
  method: GET
  value_template: "{{ value_json.decision.tp | default('--') }}"
  unit_of_measurement: "USDT"
  scan_interval: 30
  timeout: 10

- platform: rest
  name: "S25 ARKON5 SL"
  unique_id: s25_arkon5_sl
  resource: "http://homeassistant.local:8123/local/ai_analysis.json"
  method: GET
  value_template: "{{ value_json.decision.sl | default('--') }}"
  unit_of_measurement: "USDT"
  scan_interval: 30
  timeout: 10

- platform: rest
  name: "S25 ARKON5 Reason"
  unique_id: s25_arkon5_reason
  resource: "http://homeassistant.local:8123/local/ai_analysis.json"
  method: GET
  value_template: "{{ value_json.decision.reason | default('En attente') }}"
  scan_interval: 30
  timeout: 10

- platform: rest
  name: "S25 Pipeline Timestamp"
  unique_id: s25_pipeline_timestamp
  resource: "http://homeassistant.local:8123/local/ai_analysis.json"
  method: GET
  value_template: "{{ value_json.timestamp | default(0) | timestamp_local }}"
  scan_interval: 30
  timeout: 10
EOF
    ok "Sensors S25 ajoutés à $SENSORS_FILE"
fi

# ─────────────────────────────────────────
# 4. ai_analysis.json — Fichier initial
# ─────────────────────────────────────────
log "4. Création ai_analysis.json initial..."
cat > /config/www/ai_analysis.json << 'EOF'
{
  "decision": {
    "action": "HOLD",
    "conf": 0.0,
    "tp": null,
    "sl": null,
    "size": 0.0,
    "reason": "S25 ARKON-5 initialisé — en attente signal Kimi"
  },
  "signal": {
    "source": "init",
    "strength": "weak",
    "trend": "neutral"
  },
  "timestamp": 0,
  "model": "ARKON-5/init",
  "version": "2.0"
}
EOF
ok "ai_analysis.json créé dans /config/www/"

# ─────────────────────────────────────────
# 5. VÉRIFICATION secrets.yaml
# ─────────────────────────────────────────
log "5. Vérification secrets.yaml..."
SECRETS="/config/secrets.yaml"
KEYS_NEEDED=("gemini_api_key" "ha_long_lived_token" "mexc_api_key" "mexc_secret")
MISSING=0

for key in "${KEYS_NEEDED[@]}"; do
    if grep -q "^${key}:" "$SECRETS" 2>/dev/null; then
        ok "  $key ✓"
    else
        warn "  $key MANQUANT dans secrets.yaml"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    warn "$MISSING clé(s) manquante(s) dans secrets.yaml"
    warn "Ajouter manuellement dans $SECRETS"
fi

# ─────────────────────────────────────────
# 6. RELOAD HA
# ─────────────────────────────────────────
log "6. Reload Home Assistant..."
# Via API HA locale
if curl -s -X POST \
    "http://172.30.32.1:8123/api/services/homeassistant/reload_config_entry" \
    -H "Authorization: Bearer ${HA_TOKEN}" \
    -H "Content-Type: application/json" \
    --silent --output /dev/null --write-out "%{http_code}" | grep -q "200\|201"; then
    ok "HA reload OK"
else
    warn "Reload HA manuel requis: Settings → System → Restart"
fi

# ─────────────────────────────────────────
# RÉSUMÉ
# ─────────────────────────────────────────
echo ""
log "======================================"
log "✅ S25 LUMIÈRE — Déploiement terminé!"
log "======================================"
log ""
log "Prochaines étapes:"
log "  1. Compléter secrets.yaml avec les clés API"
log "  2. Restart HA: Settings → System → Restart"
log "  3. Ajouter dashboard Lovelace (s25_dashboard_lovelace.yaml)"
log "  4. Démarrer tunnel: bash /config/scripts/start_s25_tunnel.sh"
log "  5. Vérifier sensors: Developer Tools → States → s25"
log ""
log "Dashboard S25 Lumière: http://homeassistant.local:8123/lovelace/s25_orchestrator"
log "======================================"
