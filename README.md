# ⚡ S25-COMMAND-CENTER — Full Agentique

```
╔═══════════════════════════════════════════════════════╗
║         S25 LUMIÈRE — ARKON-5 COMMAND CENTER          ║
║         Major Stef // Build: Claude // 2026           ║
╚═══════════════════════════════════════════════════════╝
```

## 🏗️ Architecture Multi-Agents

```
KIMI WEB3 (Signal)
    ↓ HTTPS Cloudflare Tunnel
HOME ASSISTANT (Hub Central HA)
    ↓ Webhook → Automation
ARKON-5 / GEMINI (Analyse IA)
    ↓ Décision BUY/SELL/HOLD
MEXC API (Exécution Trading)
    ↑
AKASH CENTOS (Watchdog + Cockpit)
    ↑
PERPLEXITY/COMET (Surveillance 24/7)
```

## 🤖 Agents Network

| Agent | Rôle | Status |
|-------|------|--------|
| **MERLIN** (Gemini) | Orchestrateur HA | 🟢 ONLINE |
| **COMET** (Perplexity) | Watchman Radar | 🟢 ACTIVE |
| **ARKON-5** (Gemini) | Analyseur Trading | 🟢 READY |
| **KIMI Web3** | Source Signaux | 🟡 SIGNAL |
| **GPT** | GOUV4 Planner | 🟢 ONLINE |
| **CLAUDE** | Builder/Deploy | 🟢 ONLINE |
| **TRINITY** | TTS Vocal HA | 🟢 ACTIVE |

## 📁 Structure

```
s25-command-center/
├── 🏠 ha/
│   ├── automations/          # Automations HA S25
│   ├── sensors/              # Sensors ARKON-5 REST
│   ├── dashboards/           # Lovelace S25 Lumière
│   └── python_scripts/
│       └── ai_router.py      # Router Multi-Modèle v2
├── 🤖 agents/
│   ├── watchdog.py           # Self-Healing CentOS
│   ├── cockpit_lumiere.py    # Web UI Futuriste :7777
│   └── gouv4_planner.py      # Governance Layer
├── ⛏️ mining/
│   └── antminer_monitor.py   # Antminer S19j REST
├── 🌐 kimi/
│   └── kimi_proxy.py         # Proxy Signal :9191
├── 📊 scripts/
│   ├── start_s25_tunnel.sh   # Tunnel Cloudflare
│   ├── deploy_s25_ha.sh      # Déploiement HA
│   └── github_sync.sh        # Auto-commit 03:00 UTC
├── 🤖 xiaomi/
│   └── deploy.yaml           # Akash VLA Robot Model
├── requirements.txt
└── .env.example
```

## 🚀 Déploiement rapide (Akash CentOS)

```bash
git clone https://github.com/stephaneboss/S25-COMMAND-CENTER
cd S25-COMMAND-CENTER
pip3 install -r requirements.txt
cp .env.example .env  # Configurer les clés API
python3 agents/watchdog.py &
python3 agents/cockpit_lumiere.py
```

## 🔐 Système T0/T1/T2/T3

| Niveau | Couleur | Condition | Action |
|--------|---------|-----------|--------|
| **T0** | 🟢 NORMAL | Tout OK | Surveillance passive |
| **T1** | 🟡 SURVEILLANCE | Conf < 40% ou SELL signal | Alerte passive |
| **T2** | 🟠 ALERTE | SELL Conf > 70% | Notification urgente |
| **T3** | 🔴 CRITIQUE | Kill switch / Disk > 90% | PURGE + Lockdown |

## ⚡ Services Déployés dans HA

### Automations S25 (9 total)
- `s25_ingestion_intel_comet` — Webhook Intel Perplexity
- `s25_alerte_monitoring_antminer` — Hashrate/Temp alerts
- `s25_protocole_de_purge` — Kill Switch total
- `s25_threat_t1_surveillance` — T1 Yellow alert
- `s25_threat_t2_alerte` — T2 Orange alert
- `s25_threat_t3_critique` — T3 Red alert + purge
- `s25_arkon5_buy_alert` — BUY signal Gemini
- `s25_arkon5_sell_alert` — SELL signal Gemini
- `s25_arkon5_hold` — HOLD standby
- `s25_daily_report_20h` — Rapport TRINITY 20h

## 📡 Cockpit Lumière

Accessible sur: `http://<akash-ip>:7777`

Interface visuelle temps réel:
- Niveau de menace T0-T3
- Signal ARKON-5 (BUY/SELL/HOLD)
- Status agents network
- Intel COMET
- Contrôles tunnel/purge

---
*Built by Claude for Major Stef — S25 Lumière Project 2026*
