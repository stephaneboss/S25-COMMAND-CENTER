#!/usr/bin/env python3
# ============================================================
# S25 LUMIÈRE — Cockpit Web UI v1.0
# Interface visuelle futuriste pour CentOS Akash
# Accessible via navigateur Web depuis le S25 Ultra
# PORT: 7777
# ============================================================

from flask import Flask, render_template_string, jsonify, request
import os, json, requests, subprocess
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "s25_lumiere_secret_x100")

HA_URL   = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")

HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ S25 LUMIÈRE — COCKPIT</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: radial-gradient(ellipse at top, #0d1b2a 0%, #0a0a0f 100%);
  color: #e0e6ff; font-family: 'Courier New', monospace;
  min-height: 100vh; overflow-x: hidden;
}
.scanlines {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,200,0.015) 2px, rgba(0,255,200,0.015) 4px);
  pointer-events: none; z-index: 1;
}
.container { max-width: 1200px; margin: 0 auto; padding: 20px; position: relative; z-index: 2; }
.header { text-align: center; margin-bottom: 30px; }
.header h1 {
  font-size: 2.5rem; color: #00ffcc;
  text-shadow: 0 0 20px #00ffcc, 0 0 40px #00ffcc;
  animation: pulse 2s ease-in-out infinite;
  letter-spacing: 0.3em;
}
@keyframes pulse {
  0%, 100% { opacity: 1; } 50% { opacity: 0.8; }
}
.subtitle { color: #4fc3f7; font-size: 0.9rem; letter-spacing: 0.2em; margin-top: 5px; }
.timestamp { color: #546e7a; font-size: 0.75rem; margin-top: 5px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 20px; }
.card {
  background: rgba(0, 255, 200, 0.05);
  border: 1px solid rgba(0, 255, 200, 0.2);
  border-radius: 12px; padding: 20px;
  transition: all 0.3s ease;
  position: relative; overflow: hidden;
}
.card:hover { border-color: rgba(0, 255, 200, 0.5); box-shadow: 0 0 20px rgba(0, 255, 200, 0.1); }
.card::before {
  content: ''; position: absolute; top: 0; left: -100%;
  width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, #00ffcc, transparent);
  animation: scan 3s linear infinite;
}
@keyframes scan { to { left: 200%; } }
.card-title { color: #00ffcc; font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 10px; }
.card-value { font-size: 2rem; font-weight: bold; color: #fff; }
.card-value.green { color: #00ff88; text-shadow: 0 0 10px #00ff88; }
.card-value.red { color: #ff4444; text-shadow: 0 0 10px #ff4444; }
.card-value.orange { color: #ff9800; text-shadow: 0 0 10px #ff9800; }
.card-value.blue { color: #4fc3f7; text-shadow: 0 0 10px #4fc3f7; }
.card-subtitle { color: #546e7a; font-size: 0.75rem; margin-top: 5px; }
.status-dot {
  width: 10px; height: 10px; border-radius: 50%;
  display: inline-block; margin-right: 8px;
  animation: blink 1s ease-in-out infinite;
}
.status-dot.green { background: #00ff88; box-shadow: 0 0 8px #00ff88; }
.status-dot.red { background: #ff4444; box-shadow: 0 0 8px #ff4444; }
.status-dot.orange { background: #ff9800; box-shadow: 0 0 8px #ff9800; }
@keyframes blink { 50% { opacity: 0.3; } }
.section-title { color: #4fc3f7; font-size: 0.9rem; letter-spacing: 0.2em; margin: 20px 0 10px; border-bottom: 1px solid rgba(79, 195, 247, 0.2); padding-bottom: 5px; }
.agents-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
.agent-card {
  background: rgba(79, 195, 247, 0.05); border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 8px; padding: 15px; text-align: center;
}
.agent-name { color: #4fc3f7; font-size: 0.85rem; letter-spacing: 0.15em; margin-bottom: 8px; }
.agent-status { font-size: 0.75rem; color: #546e7a; }
.controls { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
.btn {
  padding: 10px 20px; border: 1px solid rgba(0, 255, 200, 0.4);
  background: rgba(0, 255, 200, 0.1); color: #00ffcc;
  border-radius: 6px; cursor: pointer; font-family: 'Courier New', monospace;
  font-size: 0.8rem; letter-spacing: 0.1em; transition: all 0.2s;
}
.btn:hover { background: rgba(0, 255, 200, 0.2); box-shadow: 0 0 15px rgba(0, 255, 200, 0.3); }
.btn.red { border-color: rgba(255, 68, 68, 0.4); background: rgba(255, 68, 68, 0.1); color: #ff4444; }
.btn.red:hover { background: rgba(255, 68, 68, 0.2); }
.intel-box {
  background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(0, 255, 200, 0.15);
  border-radius: 8px; padding: 15px; font-size: 0.8rem; color: #80cbc4;
  max-height: 150px; overflow-y: auto; white-space: pre-wrap;
  font-family: 'Courier New', monospace;
}
.threat-bar {
  display: flex; gap: 5px; margin: 10px 0;
}
.threat-level {
  flex: 1; padding: 8px; border-radius: 4px; text-align: center;
  font-size: 0.7rem; letter-spacing: 0.1em; border: 1px solid transparent;
}
.threat-level.active-t0 { background: rgba(0, 255, 136, 0.2); border-color: #00ff88; color: #00ff88; }
.threat-level.active-t1 { background: rgba(255, 235, 59, 0.2); border-color: #ffeb3b; color: #ffeb3b; }
.threat-level.active-t2 { background: rgba(255, 152, 0, 0.2); border-color: #ff9800; color: #ff9800; }
.threat-level.active-t3 { background: rgba(255, 68, 68, 0.2); border-color: #ff4444; color: #ff4444; }
.threat-level.inactive { background: rgba(255,255,255,0.02); border-color: rgba(255,255,255,0.05); color: #37474f; }
footer { text-align: center; color: #263238; font-size: 0.7rem; margin-top: 30px; letter-spacing: 0.2em; }
</style>
</head>
<body>
<div class="scanlines"></div>
<div class="container">
  <div class="header">
    <h1>⚡ S25 LUMIÈRE</h1>
    <div class="subtitle">ARKON-5 COMMAND CENTER // COCKPIT v1.0</div>
    <div class="timestamp" id="clock">--</div>
  </div>

  <!-- THREAT LEVEL BAR -->
  <div id="threat-bar" class="threat-bar">
    <div class="threat-level active-t0">T0 🟢 NORMAL</div>
    <div class="threat-level inactive">T1 🟡 SURVEILLANCE</div>
    <div class="threat-level inactive">T2 🟠 ALERTE</div>
    <div class="threat-level inactive">T3 🔴 CRITIQUE</div>
  </div>

  <!-- STATUS CARDS -->
  <div class="grid" id="status-grid">
    <div class="card">
      <div class="card-title">🎯 SIGNAL ARKON-5</div>
      <div class="card-value" id="arkon-action">--</div>
      <div class="card-subtitle" id="arkon-conf">Confiance: --</div>
    </div>
    <div class="card">
      <div class="card-title">📊 PIPELINE S25</div>
      <div class="card-value blue" id="pipeline-status">--</div>
      <div class="card-subtitle">Modèle actif</div>
    </div>
    <div class="card">
      <div class="card-title">⛏️ HASHRATE</div>
      <div class="card-value orange" id="hashrate">-- TH/s</div>
      <div class="card-subtitle" id="temp">Temp: --°C</div>
    </div>
    <div class="card">
      <div class="card-title">🌐 TUNNEL S25</div>
      <div class="card-value" id="tunnel-status">--</div>
      <div class="card-subtitle">Cloudflare ↔ Kimi</div>
    </div>
  </div>

  <!-- AGENTS STATUS -->
  <div class="section-title">⟐ AGENTS NETWORK</div>
  <div class="agents-grid">
    <div class="agent-card">
      <div class="agent-name">🤖 MERLIN</div>
      <div><span class="status-dot green"></span><span class="agent-status">Orchestrateur HA</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">🔭 COMET</div>
      <div><span class="status-dot green"></span><span class="agent-status">Watchman Radar</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">🧠 GEMINI</div>
      <div><span class="status-dot green"></span><span class="agent-status">ARKON-5 Analyzer</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">🌐 KIMI Web3</div>
      <div><span class="status-dot orange"></span><span class="agent-status">Signal Source</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">🤝 GPT</div>
      <div><span class="status-dot green"></span><span class="agent-status">GOUV4 Planner</span></div>
    </div>
    <div class="agent-card">
      <div class="agent-name">⚡ CLAUDE</div>
      <div><span class="status-dot green"></span><span class="agent-status">Builder / Deploy</span></div>
    </div>
  </div>

  <!-- COMET INTEL -->
  <div class="section-title">📡 INTEL COMET</div>
  <div class="intel-box" id="comet-intel">En attente de connexion HA...</div>

  <!-- CONTRÔLES -->
  <div class="section-title">🎛️ CONTRÔLES</div>
  <div class="controls">
    <button class="btn" onclick="startTunnel()">▶ START TUNNEL</button>
    <button class="btn" onclick="stopTunnel()">⬛ STOP TUNNEL</button>
    <button class="btn" onclick="refreshData()">⟳ REFRESH</button>
    <button class="btn" onclick="forceAnalysis()">🧠 FORCE ANALYSE</button>
    <button class="btn red" onclick="confirmPurge()">🚨 PURGE (KILL)</button>
  </div>

  <footer>S25 LUMIÈRE COCKPIT v1.0 // AKASH CENTOS // CLAUDE BUILD // {{ now }}</footer>
</div>

<script>
// Auto-refresh toutes les 30s
let refreshTimer = setInterval(refreshData, 30000);

function updateClock() {
  document.getElementById('clock').textContent = new Date().toLocaleString('fr-CA');
}
setInterval(updateClock, 1000);
updateClock();

async function refreshData() {
  try {
    const r = await fetch('/api/status');
    const data = await r.json();

    // Arkon action
    const action = data.arkon5_action || 'HOLD';
    const actionEl = document.getElementById('arkon-action');
    actionEl.textContent = action;
    actionEl.className = 'card-value ' + (action === 'BUY' ? 'green' : action === 'SELL' ? 'red' : 'orange');

    document.getElementById('arkon-conf').textContent = 'Confiance: ' + (data.arkon5_conf || '--') + '%';
    document.getElementById('pipeline-status').textContent = (data.pipeline_status || '--').substring(0, 20);
    document.getElementById('hashrate').textContent = (data.hashrate || '--') + ' TH/s';
    document.getElementById('temp').textContent = 'Temp: ' + (data.temp || '--') + '°C';
    document.getElementById('comet-intel').textContent = data.comet_intel || '--';

    const tunnelEl = document.getElementById('tunnel-status');
    tunnelEl.textContent = data.tunnel_active ? '🟢 ACTIF' : '🔴 INACTIF';
    tunnelEl.className = 'card-value ' + (data.tunnel_active ? 'green' : 'red');

  } catch(e) {
    console.error('Refresh error:', e);
  }
}

async function startTunnel() {
  await fetch('/api/action', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'start_tunnel'}) });
  refreshData();
}
async function stopTunnel() {
  await fetch('/api/action', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'stop_tunnel'}) });
  refreshData();
}
async function forceAnalysis() {
  await fetch('/api/action', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'force_analysis'}) });
  alert('Analyse ARKON-5 déclenchée!');
}
function confirmPurge() {
  if (confirm('⚠️ CONFIRMER LA PURGE TOTALE S25? Cette action coupe toutes les opérations critiques.')) {
    fetch('/api/action', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'purge'}) });
    alert('🚨 PURGE EXÉCUTÉE');
  }
}
refreshData();
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML, now=datetime.now().strftime('%Y-%m-%d'))

@app.route('/api/status')
def api_status():
    """Retourne l'état du système S25 depuis HA"""
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "arkon5_action": "HOLD",
        "arkon5_conf": 0,
        "pipeline_status": "INIT",
        "hashrate": "--",
        "temp": "--",
        "comet_intel": "En attente...",
        "tunnel_active": False
    }

    if not HA_TOKEN:
        return jsonify(status)

    try:
        headers = {"Authorization": f"Bearer {HA_TOKEN}"}
        entities = ["sensor.s25_arkon5_action", "sensor.s25_arkon5_conf",
                    "input_text.ai_model_actif", "sensor.antminer_hashrate",
                    "sensor.antminer_temp", "input_text.s25_comet_intel"]

        for entity in entities:
            r = requests.get(f"{HA_URL}/api/states/{entity}", headers=headers, timeout=5)
            if r.status_code == 200:
                state = r.json().get("state", "--")
                if "arkon5_action" in entity: status["arkon5_action"] = state
                elif "arkon5_conf" in entity: status["arkon5_conf"] = state
                elif "ai_model_actif" in entity: status["pipeline_status"] = state
                elif "antminer_hashrate" in entity: status["hashrate"] = state
                elif "antminer_temp" in entity: status["temp"] = state
                elif "comet_intel" in entity: status["comet_intel"] = state

        # Check tunnel
        result = subprocess.run(["pgrep", "-f", "cloudflared"], capture_output=True)
        status["tunnel_active"] = result.returncode == 0

    except Exception as e:
        status["error"] = str(e)

    return jsonify(status)

@app.route('/api/action', methods=['POST'])
def api_action():
    """Exécute une action sur le système S25"""
    data = request.get_json()
    action = data.get('action', '')
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}

    if action == 'start_tunnel':
        subprocess.Popen(["bash", "/config/scripts/start_s25_tunnel.sh"])
        return jsonify({"ok": True, "msg": "Tunnel démarré"})

    elif action == 'stop_tunnel':
        subprocess.run(["pkill", "-f", "cloudflared"])
        return jsonify({"ok": True, "msg": "Tunnel arrêté"})

    elif action == 'force_analysis':
        requests.post(f"{HA_URL}/api/services/automation/trigger",
                     headers=headers, json={"entity_id": "automation.s25_arkon5_buy_alert"})
        return jsonify({"ok": True, "msg": "Analyse déclenchée"})

    elif action == 'purge':
        requests.post(f"{HA_URL}/api/services/input_boolean/turn_on",
                     headers=headers, json={"entity_id": "input_boolean.s25_kill_switch"})
        return jsonify({"ok": True, "msg": "PURGE EXÉCUTÉE"})

    return jsonify({"ok": False, "msg": "Action inconnue"})

@app.route('/api/watchdog')
def api_watchdog():
    """Retourne le statut du watchdog"""
    try:
        with open('/tmp/s25_watchdog_status.json') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({"error": "Watchdog status unavailable"})

if __name__ == '__main__':
    port = int(os.getenv("PORT", "7777"))
    app.run(host='0.0.0.0', port=port, debug=False)
