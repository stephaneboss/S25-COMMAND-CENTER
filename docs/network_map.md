# S25 Lumière — Network Map (Confirmé 2026-03-07)

> Scan autonome par **Codex CLI** depuis le poste Windows S25. Infrastructure 100% confirmée live.

## Topologie Réseau

```
Internet
    │
    ├── Akash Network (Public)
    │   └── Open WebUI 0.8.5
    │       URL: https://tlravugbk59r7eqghunmr1u2ks.ingress.akash-palmito.org
    │
LAN 10.0.0.x
    │
    ├── 10.0.0.1 — Gateway/Router
    │   └── :1883 MQTT
    │
    ├── 10.0.0.136 — Home Assistant Hub S25
    │   ├── :8123 HA Frontend (auth protégé)
    │   └── :1883 MQTT
    │
    └── 10.0.0.202 — DELL-LINUX (Serveur IA Principal)
        ├── :22   SSH
        ├── :3000 Grafana 12.4.0
        ├── :3001 dashdot (monitoring système)
        ├── :3002 Open WebUI 0.7.2 (LLM local, auth ON)
        ├── :5000 Webhook GPT (Flask "Webhook GPT opérationnel")
        └── :11434 Ollama
                ├── major-llama:latest
                └── llama3:latest
```

## Services Critiques Pipeline S25

| Service | Host | Port | Rôle S25 |
|---------|------|------|----------|
| Home Assistant | 10.0.0.136 | 8123 | Hub central, automations, entités |
| MQTT | 10.0.0.136 | 1883 | Messages IoT |
| Webhook GPT | 10.0.0.202 | 5000 | Entrée signals GPT/TRINITY |
| Ollama | 10.0.0.202 | 11434 | LLM local gratuit (agent_loop.py) |
| Open WebUI local | 10.0.0.202 | 3002 | Interface LLM pour Stef |
| Grafana | 10.0.0.202 | 3000 | Monitoring pipeline |
| Open WebUI public | Akash | 443 | Accès externe LLM |

## Variables d'environnement S25 (à configurer)

```bash
# DELL-LINUX / Akash
export COCKPIT_URL="http://10.0.0.202:5000"        # Webhook GPT (LAN)
export COCKPIT_URL_PUBLIC="https://tlravugbk59r7eqghunmr1u2ks.ingress.akash-palmito.org"
export HA_URL="http://10.0.0.136:8123"
export HA_TOKEN="<long-lived-token>"               # À créer dans HA
export OLLAMA_URL="http://10.0.0.202:11434"        # Ollama local
export OLLAMA_MODEL="major-llama"                   # ou llama3
export MEXC_DRY_RUN="true"                         # Toujours true en test

# Ports services COMET Bridge
export COMET_PORT="5100"

# MQTT (si utilisé par agents)
export MQTT_HOST="10.0.0.136"
export MQTT_PORT="1883"
```

## Connexions Inter-Services

```
TRINITY (GPT laptop)
  → Codex CLI local
  → DELL-LINUX:5000 Webhook GPT
  → HA 10.0.0.136:8123 API

ARKON (Claude Code sur DELL-LINUX)
  → Analyse logs /tmp/
  → DELL-LINUX:11434 Ollama
  → DELL-LINUX:5000 cockpit local

COMET (Perplexity)
  → comet_bridge.py :5100
  → DELL-LINUX:5000 cockpit
  → HA 10.0.0.136:8123

agent_loop.py
  → CoinGecko (internet)
  → Fear&Greed (internet)
  → Reddit RSS (internet)
  → DELL-LINUX:11434 Ollama (LAN, GRATUIT)
  → DELL-LINUX:5000 cockpit

KIMI (Web3 Scanner)
  → Cloudflare Tunnel → kimi_proxy.py :9191
  → HA Webhook :8123/api/webhook/s25_kimi_scan_secret_xyz
```

## Prochains Branchements

1. **HA_TOKEN** — Extraire via browser JS ou créer Long-Lived Token
2. **agent_loop.py** — Déployer sur DELL-LINUX avec Ollama local
3. **comet_bridge.py** — Déployer sur DELL-LINUX :5100
4. **Grafana** — Ajouter dashboards S25 (signaux, P&L, threat level)
5. **MQTT** — Brancher automations HA vers pipeline via MQTT
