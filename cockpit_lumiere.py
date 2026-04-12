#!/usr/bin/env python3
# ============================================================
# S25 LUMIÈRE — Cockpit Web UI v1.0
# Interface visuelle futuriste pour CentOS Akash
# Accessible via navigateur Web depuis le S25 Ultra
# PORT: 7777
# ============================================================

from flask import Flask, render_template_string, jsonify, request
import os, json, requests, subprocess, uuid
from datetime import datetime, timezone
from pathlib import Path
from security.vault import vault_get

MEMORY_DIR = Path(os.getenv("MEMORY_DIR", "/app/memory"))
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SHARED_MEMORY_FILE = MEMORY_DIR / "SHARED_MEMORY.md"
AGENTS_STATE_FILE  = MEMORY_DIR / "agents_state.json"

app = Flask(__name__)
app.secret_key = vault_get("SECRET_KEY", os.urandom(32).hex())

HA_URL          = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN        = vault_get("HA_TOKEN", "")
GEMINI_API_KEY  = vault_get("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
S25_SECRET      = vault_get("S25_SHARED_SECRET", "")
APP_BUILD_SHA   = os.getenv("APP_BUILD_SHA", "dev")
ALLOW_PUBLIC_ACTIONS = os.getenv("ALLOW_PUBLIC_ACTIONS", "true").lower() in {"1", "true", "yes", "on"}


def _process_running(process_name: str) -> bool:
    """Portable process check that works on slim images without pgrep."""
    try:
        result = subprocess.run(
            ["ps", "-ef"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return False

    return process_name in result.stdout

HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>S25 LUMIERE - COCKPIT</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:radial-gradient(ellipse at top,#0d1b2a 0%,#0a0a0f 100%);color:#e0e6ff;font-family:'Courier New',monospace;min-height:100vh;overflow-x:hidden}
.scanlines{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,200,.015) 2px,rgba(0,255,200,.015) 4px);pointer-events:none;z-index:1}
.container{max-width:1400px;margin:0 auto;padding:15px;position:relative;z-index:2}
.header{text-align:center;margin-bottom:20px}
.header h1{font-size:2.2rem;color:#00ffcc;text-shadow:0 0 20px #00ffcc,0 0 40px #00ffcc;animation:pulse 2s ease-in-out infinite;letter-spacing:.3em}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.8}}
.subtitle{color:#4fc3f7;font-size:.85rem;letter-spacing:.2em;margin-top:4px}
.timestamp{color:#546e7a;font-size:.7rem;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:15px}
.card{background:rgba(0,255,200,.05);border:1px solid rgba(0,255,200,.2);border-radius:10px;padding:14px;transition:all .3s;position:relative;overflow:hidden}
.card:hover{border-color:rgba(0,255,200,.5);box-shadow:0 0 20px rgba(0,255,200,.1)}
.card::before{content:'';position:absolute;top:0;left:-100%;width:100%;height:2px;background:linear-gradient(90deg,transparent,#00ffcc,transparent);animation:scan 3s linear infinite}
@keyframes scan{to{left:200%}}
.card-title{color:#00ffcc;font-size:.72rem;letter-spacing:.15em;margin-bottom:6px}
.card-value{font-size:1.5rem;font-weight:bold;color:#fff}
.green{color:#00ff88;text-shadow:0 0 10px #00ff88}.red{color:#ff4444;text-shadow:0 0 10px #ff4444}.orange{color:#ff9800;text-shadow:0 0 10px #ff9800}.blue{color:#4fc3f7;text-shadow:0 0 10px #4fc3f7}
.card-sub{color:#546e7a;font-size:.68rem;margin-top:3px}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px}
.dot.on{background:#00ff88;box-shadow:0 0 6px #00ff88}.dot.standby{background:#ff9800;box-shadow:0 0 6px #ff9800}.dot.off{background:#ff4444;box-shadow:0 0 6px #ff4444}
.section{color:#4fc3f7;font-size:.82rem;letter-spacing:.2em;margin:15px 0 8px;border-bottom:1px solid rgba(79,195,247,.2);padding-bottom:4px}
.svc-bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.svc-link{padding:7px 14px;border:1px solid rgba(0,255,200,.3);background:rgba(0,255,200,.08);color:#00ffcc;border-radius:6px;text-decoration:none;font-family:'Courier New',monospace;font-size:.72rem;letter-spacing:.1em;transition:all .2s}
.svc-link:hover{background:rgba(0,255,200,.2);box-shadow:0 0 12px rgba(0,255,200,.2)}
.agents-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:12px}
.ag{background:rgba(79,195,247,.05);border:1px solid rgba(79,195,247,.15);border-radius:7px;padding:10px;text-align:center;transition:all .2s}
.ag:hover{border-color:rgba(79,195,247,.4);transform:translateY(-1px)}
.ag.on{border-color:rgba(0,255,136,.3)}.ag.standby{border-color:rgba(255,152,0,.2)}
.ag-name{color:#4fc3f7;font-size:.75rem;letter-spacing:.08em;margin-bottom:4px}
.ag-info{font-size:.65rem;color:#546e7a}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:768px){.two-col{grid-template-columns:1fr}}
.intel-box{background:rgba(0,0,0,.4);border:1px solid rgba(0,255,200,.15);border-radius:8px;padding:10px;font-size:.72rem;color:#80cbc4;height:280px;overflow-y:auto;white-space:pre-wrap;font-family:'Courier New',monospace}
.jarvis-box{background:rgba(0,0,0,.5);border:1px solid rgba(79,195,247,.3);border-radius:10px;padding:12px;display:flex;flex-direction:column;height:280px}
.j-msgs{flex:1;overflow-y:auto;margin-bottom:8px;font-size:.78rem;line-height:1.4}
.j-msgs .m{margin-bottom:6px;padding:5px 9px;border-radius:6px;max-width:85%;word-wrap:break-word}
.m.u{background:rgba(0,255,200,.1);color:#00ffcc;margin-left:auto}
.m.a{background:rgba(79,195,247,.1);color:#e0e6ff}
.j-in{display:flex;gap:6px}
.j-in input{flex:1;padding:7px 10px;background:rgba(255,255,255,.05);border:1px solid rgba(79,195,247,.3);border-radius:6px;color:#e0e6ff;font-family:'Courier New',monospace;font-size:.78rem;outline:none}
.j-in input:focus{border-color:#4fc3f7}
.j-in button{padding:7px 14px;background:rgba(79,195,247,.2);border:1px solid rgba(79,195,247,.4);border-radius:6px;color:#4fc3f7;cursor:pointer;font-family:'Courier New',monospace;font-size:.78rem}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.btn{padding:7px 14px;border:1px solid rgba(0,255,200,.4);background:rgba(0,255,200,.1);color:#00ffcc;border-radius:6px;cursor:pointer;font-family:'Courier New',monospace;font-size:.72rem;letter-spacing:.1em;transition:all .2s}
.btn:hover{background:rgba(0,255,200,.2);box-shadow:0 0 12px rgba(0,255,200,.2)}
.btn.red{border-color:rgba(255,68,68,.4);background:rgba(255,68,68,.1);color:#ff4444}
footer{text-align:center;color:#263238;font-size:.6rem;margin-top:15px;letter-spacing:.15em}
.typing{display:inline-block;width:12px;animation:typingAnim .8s steps(3) infinite}
@keyframes typingAnim{0%{content:'.'} 33%{content:'..'} 66%{content:'...'}}
</style>
</head>
<body>
<div class="scanlines"></div>
<div class="container">
  <div class="header">
    <h1>S25 LUMIERE</h1>
    <div class="subtitle">COMMAND CENTER // AlienStef Node</div>
    <div class="timestamp" id="clock">--</div>
  </div>

  <div class="section">SERVICES</div>
  <div class="svc-bar">
    <a class="svc-link" href="https://alien.smajor.org" target="_blank">Open WebUI</a>
    <a class="svc-link" href="https://jarvis.smajor.org/docs" target="_blank">Jarvis API</a>
    <a class="svc-link" href="https://api-alien.smajor.org" target="_blank">Bras-Alien</a>
    <a class="svc-link" href="https://cockpit-alien.smajor.org" target="_blank">Cockpit</a>
    <a class="svc-link" href="https://s25.smajor.org" target="_blank">Akash</a>
    <a class="svc-link" href="https://app.smajor.org" target="_blank">Admin</a>
    <a class="svc-link" href="https://smajor.org" target="_blank">smajor.org</a>
  </div>

  <div class="grid" id="status-grid">
    <div class="card"><div class="card-title">MESH AGENTS</div><div class="card-value green" id="mesh-count">--</div><div class="card-sub" id="mesh-detail">loading...</div></div>
    <div class="card"><div class="card-title">BRAS-ALIEN</div><div class="card-value blue" id="fleet-count">--</div><div class="card-sub" id="fleet-detail">--</div></div>
    <div class="card"><div class="card-title">OLLAMA</div><div class="card-value green" id="ollama-status">--</div><div class="card-sub" id="ollama-models">--</div></div>
    <div class="card"><div class="card-title">ARKON-5</div><div class="card-value orange" id="arkon-action">HOLD</div><div class="card-sub" id="arkon-conf">--</div></div>
    <div class="card"><div class="card-title">TUNNEL CF</div><div class="card-value" id="tunnel-status">--</div><div class="card-sub">s25-alien</div></div>
    <div class="card"><div class="card-title">SYSTEM</div><div class="card-value blue" id="sys-info">--</div><div class="card-sub" id="sys-detail">--</div></div>
  </div>

  <div class="section">AGENT MESH</div>
  <div class="agents-grid" id="agents-grid"><div class="ag"><div class="ag-name">Loading...</div></div></div>

  <div class="section">JARVIS + INTEL</div>
  <div class="two-col">
    <div class="jarvis-box">
      <div class="j-msgs" id="j-msgs"><div class="m a">Jarvis S25 pret. Pose ta question.</div></div>
      <div class="j-in"><input type="text" id="j-in" placeholder="Parle a Jarvis..." onkeydown="if(event.key==='Enter')sendJ()"><button onclick="sendJ()">SEND</button></div>
    </div>
    <div class="intel-box" id="intel-log">En attente...</div>
  </div>

  <div class="section">CONTROLS</div>
  <div class="controls">
    <button class="btn" onclick="refreshData()">REFRESH</button>
    <button class="btn" onclick="forceAnalysis()">FORCE ANALYSE</button>
    <button class="btn" onclick="rebuildMem()">REBUILD MEMORY</button>
    <button class="btn red" onclick="if(confirm('PURGE TOTALE?'))fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'purge'})})">PURGE</button>
  </div>

  <footer>S25 LUMIERE COCKPIT v2.0 // AlienStef + Akash // {{ now }}</footer>
</div>
<script>
setInterval(()=>{document.getElementById('clock').textContent=new Date().toLocaleString('fr-CA')},1000);

async function refreshData(){
  try{
    const mesh=await(await fetch('/api/mesh/status')).json();
    const m=mesh.mesh||{};
    document.getElementById('mesh-count').textContent=m.online+'/'+m.total_agents;
    document.getElementById('mesh-detail').textContent=m.online+' online, '+m.offline+' standby';
    const ag=m.agents||{};
    const grid=document.getElementById('agents-grid');
    grid.innerHTML='';
    for(const[n,i]of Object.entries(ag).sort()){
      const s=i.status||'?';
      const d=s==='online'?'on':s==='standby'?'standby':'off';
      const t=i.last_seen?i.last_seen.substring(11,19):'--';
      grid.innerHTML+='<div class="ag '+d+'"><div class="ag-name">'+n+'</div><div><span class="dot '+d+'"></span><span class="ag-info">'+s+' '+t+'</span></div></div>';
    }
  }catch(e){console.error(e)}
  try{
    const st=await(await fetch('/api/status')).json();
    const a=st.arkon5_action||'HOLD';
    const ae=document.getElementById('arkon-action');
    ae.textContent=a;ae.className='card-value '+(a==='BUY'?'green':a==='SELL'?'red':'orange');
    document.getElementById('arkon-conf').textContent='Conf: '+(st.arkon5_conf||'--')+'%';
    const te=document.getElementById('tunnel-status');
    te.textContent=st.tunnel_active?'ACTIF':'--';te.className='card-value '+(st.tunnel_active?'green':'orange');
    if(st.ram_used)document.getElementById('sys-info').textContent=st.ram_used;
    if(st.disk_pct)document.getElementById('sys-detail').textContent='Disk: '+st.disk_pct;
  }catch(e){}
}

async function sendJ(){
  const inp=document.getElementById('j-in');
  const msg=inp.value.trim();if(!msg)return;inp.value='';
  const box=document.getElementById('j-msgs');
  box.innerHTML+='<div class="m u">'+msg.replace(/</g,'&lt;')+'</div>';
  box.scrollTop=box.scrollHeight;
  box.innerHTML+='<div class="m a" id="j-typing">...</div>';
  try{
    const r=await fetch('/api/jarvis',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
    const d=await r.json();
    document.getElementById('j-typing').remove();
    box.innerHTML+='<div class="m a">'+((d.reply||d.error||'...').replace(/</g,'&lt;'))+'</div>';
  }catch(e){
    document.getElementById('j-typing').remove();
    box.innerHTML+='<div class="m a" style="color:#ff4444">Erreur: '+e.message+'</div>';
  }
  box.scrollTop=box.scrollHeight;
}

async function forceAnalysis(){await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'force_analysis'})});refreshData()}
async function rebuildMem(){await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'rebuild_memory'})});alert('Memory rebuild triggered')}

refreshData();setInterval(refreshData,30000);
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

        # Check tunnel: try local process first (HA container), then fallback
        # to comet_intel state (Akash container — cloudflared runs on HA side).
        tunnel_active = _process_running("cloudflared")
        if not tunnel_active:
            ci = status.get("comet_intel", "")
            if "ACTIF" in ci or "trycloudflare.com" in ci:
                tunnel_active = True
        status["tunnel_active"] = tunnel_active

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

@app.route('/api/version', methods=['GET'])
def api_version():
    """Expose la version runtime pour verifier l'image active sur Akash."""
    return jsonify({
        "service": "S25 Lumiere Cockpit",
        "version": "2.0.0",
        "build_sha": APP_BUILD_SHA,
        "memory_routes": True,
        "secret_configured": bool(S25_SECRET),
    })


@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def api_health():
    """Compat health endpoint for providers and external checks."""
    return jsonify({
        "status": "ok",
        "version": "2.0.0",
        "build_sha": APP_BUILD_SHA,
    })


# ═══════════════════════════════════════════════════════════════
#  TRINITY BRIDGE — GPT Custom Action endpoint
#  TRINITY (GPT) parle ici -> S25 reseau repond
# ═══════════════════════════════════════════════════════════════

def _trinity_auth() -> bool:
    """Verifie S25_SHARED_SECRET si configure."""
    if ALLOW_PUBLIC_ACTIONS or not S25_SECRET:
        return True
    return request.headers.get("X-S25-Secret", "") == S25_SECRET

def _merlin_query(prompt: str) -> str:
    """Appel direct Merlin (Gemini) pour reponse intelligente."""
    if not GEMINI_API_KEY:
        return "MERLIN OFFLINE: GEMINI_API_KEY non configuree"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        r = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        if r.status_code == 200:
            candidates = r.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Merlin error: {e}"
    return "Merlin: pas de reponse"

def _market_snapshot() -> dict:
    """Snapshot marche crypto gratuit via CoinGecko + Fear&Greed."""
    snapshot = {"timestamp": datetime.utcnow().isoformat(), "prices": {}, "fear_greed": {}, "source": "ninja_free"}
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,akash-network,cosmos,solana",
                    "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10)
        if r.status_code == 200:
            snapshot["prices"] = r.json()
    except:
        pass
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        if r.status_code == 200:
            d = r.json()["data"][0]
            snapshot["fear_greed"] = {"value": d["value"], "label": d["value_classification"]}
    except:
        pass
    return snapshot

@app.route('/api/trinity/ping', methods=['GET'])
def trinity_ping():
    """Healthcheck pour GPT Custom Action."""
    return jsonify({
        "ok": True,
        "service": "S25 Lumiere — TRINITY Bridge",
        "version": "2.0.0",
        "merlin": "online" if GEMINI_API_KEY else "offline",
        "ha": "connected" if HA_TOKEN else "disconnected",
    })

@app.route('/api/trinity', methods=['POST'])
def trinity_dispatch():
    """
    Endpoint principal TRINITY (GPT).
    Body JSON:
      intent  : texte de l'intention de Stef
      action  : "query" | "signal" | "analyze" | "status"
      data    : {} payload optionnel
    """
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body   = request.get_json(silent=True) or {}
    intent = body.get("intent", "").strip()
    action = body.get("action", "query").lower()
    data   = body.get("data", {})

    # ── STATUS: etat du systeme ──────────────────────────────────────
    if action == "status":
        snap = _market_snapshot()
        return jsonify({
            "ok": True,
            "action": "status",
            "system": {
                "ha_connected": bool(HA_TOKEN),
                "merlin_online": bool(GEMINI_API_KEY),
                "cockpit": "ACTIVE",
            },
            "market": snap,
        })

    # ── ANALYZE: Merlin analyse un intent specifique ─────────────────
    if action == "analyze":
        snap = _market_snapshot()
        prices = snap.get("prices", {})
        btc = prices.get("bitcoin", {}).get("usd", 0)
        eth = prices.get("ethereum", {}).get("usd", 0)
        fg  = snap.get("fear_greed", {})
        prompt = f"""Tu es MERLIN, analyste senior du reseau S25 Lumiere (multi-agent crypto trading).
Stef te demande: "{intent}"

Contexte marche actuel:
- BTC: ${btc:,.0f} USD
- ETH: ${eth:,.2f} USD
- Fear & Greed: {fg.get('value','?')}/100 ({fg.get('label','?')})

Reponds de facon concise et actionnable. Donne une recommandation claire (BUY/HOLD/SELL/WATCH) si applicable."""
        analysis = _merlin_query(prompt)
        return jsonify({
            "ok": True,
            "action": "analyze",
            "intent": intent,
            "merlin_response": analysis,
            "market_context": snap,
        })

    # ── SIGNAL: injection d'un signal de trade ───────────────────────
    if action == "signal":
        signal_data = {
            "type":   "MANUAL",
            "source": "TRINITY_GPT",
            "data": {
                "intent":     intent,
                "trade_action": data.get("trade_action", "HOLD"),
                "symbol":     data.get("symbol", ""),
                "confidence": data.get("confidence", 0.7),
                "reason":     intent,
            },
            "ts": datetime.utcnow().isoformat(),
        }
        # Push vers HA si connecte
        if HA_TOKEN:
            try:
                requests.post(
                    f"{HA_URL}/api/states/sensor.s25_trinity_signal",
                    headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
                    json={"state": data.get("trade_action", "HOLD"),
                          "attributes": {"intent": intent, "source": "TRINITY", "ts": signal_data["ts"]}},
                    timeout=5)
            except:
                pass
        return jsonify({"ok": True, "action": "signal", "signal": signal_data})

    # ── QUERY: snapshot intel + reponse Merlin (default) ────────────
    snap = _market_snapshot()
    prices = snap.get("prices", {})
    btc = prices.get("bitcoin", {}).get("usd", 0)
    btc_chg = prices.get("bitcoin", {}).get("usd_24h_change", 0)
    eth = prices.get("ethereum", {}).get("usd", 0)
    fg  = snap.get("fear_greed", {})

    merlin_prompt = f"""Tu es MERLIN du reseau S25 Lumiere. Stef dit: "{intent or 'Donne-moi un update marche'}"

BTC: ${btc:,.0f} ({btc_chg:+.1f}% 24h) | ETH: ${eth:,.2f} | F&G: {fg.get('value','?')}/100 {fg.get('label','')}

Reponds en 2-3 phrases max, direct et actionnable."""

    merlin_resp = _merlin_query(merlin_prompt) if intent else "Pret a recevoir tes ordres, Stef."

    return jsonify({
        "ok": True,
        "action": "query",
        "intent": intent,
        "merlin_response": merlin_resp,
        "market": snap,
    })




# ═══════════════════════════════════════════════════════════════
#  MEMORY SYSTEM — Mémoire persistante centralisée S25
#  Tous les agents lisent/écrivent ici
#  GET  /api/memory         → contexte complet
#  GET  /api/memory/state   → état runtime agents_state.json
#  POST /api/memory/state   → mise à jour état par un agent
# ═══════════════════════════════════════════════════════════════

def _load_agents_state() -> dict:
    """Charge agents_state.json depuis disque."""
    state = {}
    try:
        if AGENTS_STATE_FILE.exists():
            state = json.loads(AGENTS_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    state.setdefault("agents", {})
    state.setdefault("pipeline", {})
    return state

def _save_agents_state(state: dict):
    """Sauvegarde agents_state.json sur disque."""
    state.setdefault("_meta", {})["updated_at"] = datetime.now(timezone.utc).isoformat()
    AGENTS_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


@app.route('/api/memory', methods=['GET'])
def api_memory_get():
    """Retourne le contexte partagé complet (SHARED_MEMORY.md + agents_state.json)."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    shared_md = ""
    if SHARED_MEMORY_FILE.exists():
        shared_md = SHARED_MEMORY_FILE.read_text(encoding="utf-8")

    state = _load_agents_state()

    return jsonify({
        "ok": True,
        "shared_memory": shared_md,
        "agents_state": state,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    })


@app.route('/api/memory/state', methods=['GET'])
def api_memory_state_get():
    """Retourne uniquement agents_state.json (léger, pour polling fréquent)."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    return jsonify({"ok": True, "state": _load_agents_state()})


@app.route('/api/memory/state', methods=['POST'])
def api_memory_state_post():
    """
    Un agent met à jour son état ou une section du state.
    Body JSON attendu:
      agent   : "TRINITY" | "ARKON" | "MERLIN" | "COMET" | "KIMI"
      updates : dict — champs à fusionner dans agents[agent]
      pipeline: dict (optionnel) — champs pipeline à mettre à jour
    """
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    agent   = body.get("agent", "").upper()
    updates = body.get("updates", {})
    pipeline_updates = body.get("pipeline", {})

    state = _load_agents_state()

    if agent:
        state["agents"].setdefault(agent, {"status": "unknown", "registered_at": datetime.now(timezone.utc).isoformat()})
        state["agents"][agent].update(updates)
        state["agents"][agent]["last_seen"] = datetime.now(timezone.utc).isoformat()

    if pipeline_updates and "pipeline" in state:
        state["pipeline"].update(pipeline_updates)

    _save_agents_state(state)

    return jsonify({"ok": True, "agent": agent, "state": state.get("agents", {}).get(agent, {})})


@app.route('/api/memory/ping', methods=['POST'])
def api_memory_ping():
    """Agent envoie un heartbeat — met à jour last_seen seulement."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body  = request.get_json(silent=True) or {}
    agent = body.get("agent", "").upper()
    state = _load_agents_state()

    if agent in state.get("agents", {}):
        state["agents"][agent]["last_seen"] = datetime.now(timezone.utc).isoformat()
        state["agents"][agent]["status"] = "online"
        _save_agents_state(state)
        return jsonify({"ok": True, "agent": agent, "ts": datetime.now(timezone.utc).isoformat()})

    return jsonify({"ok": False, "error": f"Agent {agent} inconnu"}), 404


# ═══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS — missions, intel, mesh
# ═══════════════════════════════════════════════════════════════

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_missions(state: dict) -> dict:
    """Ensure state has missions structure."""
    state.setdefault("missions", {"active": [], "history": []})
    return state


def _ensure_intel(state: dict) -> dict:
    """Ensure state has intel/comet_feed structure."""
    state.setdefault("intel", {})
    state["intel"].setdefault("comet_feed", [])
    return state


def _record_comet_intel(state: dict, summary: str, level: str = "INFO", source: str = "TRINITY") -> dict:
    """Persist COMET-style intel into shared memory for cross-agent consumption."""
    _ensure_intel(state)
    entry = {
        "ts": _utcnow_iso(),
        "source": source,
        "level": level,
        "summary": summary,
    }
    feed = state["intel"]["comet_feed"]
    feed.insert(0, entry)
    state["intel"]["comet_feed"] = feed[:50]
    return entry


def _mission_payload(body: dict) -> dict:
    """Normalize mission payload stored in shared runtime memory."""
    mission_id = body.get("mission_id") or f"mission-{uuid.uuid4().hex[:10]}"
    target = body.get("target", "COMET")
    task_type = body.get("task_type", "infra_monitoring")
    intent = body.get("intent", "").strip()
    now = _utcnow_iso()

    return {
        "mission_id": mission_id,
        "created_at": now,
        "updated_at": now,
        "created_by": body.get("created_by", "TRINITY"),
        "target": target,
        "task_type": task_type,
        "priority": body.get("priority", "normal"),
        "status": body.get("status", "queued"),
        "intent": intent,
        "context": body.get("context", {}),
        "result": body.get("result"),
    }


def _upsert_mission(state: dict, mission: dict) -> dict:
    """Insert or replace a mission in active queue."""
    _ensure_missions(state)
    missions = state["missions"]["active"]
    for index, current in enumerate(missions):
        if current.get("mission_id") == mission["mission_id"]:
            missions[index] = mission
            break
    else:
        missions.insert(0, mission)
    return mission


def _archive_mission(state: dict, mission: dict):
    """Move completed mission from active queue to history."""
    _ensure_missions(state)
    state["missions"]["active"] = [
        item for item in state["missions"]["active"]
        if item.get("mission_id") != mission.get("mission_id")
    ]
    history = state["missions"]["history"]
    history.insert(0, mission)
    state["missions"]["history"] = history[:50]


# ═══════════════════════════════════════════════════════════════
#  MESH, MISSIONS, INTEL, SIGNAL, ROUTER ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/api/mesh/status', methods=['GET'])
def api_mesh_status():
    """Vue unifiee du reseau d'agents, du pipeline et des missions."""
    state = _load_agents_state()
    _ensure_missions(state)
    _ensure_intel(state)
    agents = state.get("agents", {})
    online = sum(1 for a in agents.values() if a.get("status") == "online")
    total = len(agents)
    return jsonify({
        "ok": True,
        "mesh": {
            "total_agents": total,
            "online": online,
            "offline": total - online,
            "agents": {k: {"status": v.get("status", "unknown"), "last_seen": v.get("last_seen")} for k, v in agents.items()},
            "missions_active": len(state["missions"]["active"]),
            "intel_entries": len(state["intel"].get("comet_feed", [])),
        },
        "pipeline": state.get("pipeline", {}),
    })


@app.route('/api/missions', methods=['GET'])
def api_missions_get():
    """Liste les missions actives et l'historique recent."""
    state = _load_agents_state()
    _ensure_missions(state)
    return jsonify({
        "ok": True,
        "active": state["missions"]["active"],
        "history": state["missions"]["history"][:10],
    })


@app.route('/api/missions', methods=['POST'])
def api_missions_post():
    """Cree une mission multi-agent persistante pour COMET, MERLIN, ARKON ou KIMI."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    state = _load_agents_state()
    _ensure_missions(state)
    _ensure_intel(state)
    mission = _mission_payload(body)
    _upsert_mission(state, mission)

    target = mission["target"]
    state["agents"].setdefault(target, {})
    state["agents"][target]["last_task"] = mission["intent"]
    state["agents"][target]["last_seen"] = _utcnow_iso()
    _record_comet_intel(
        state,
        summary=f"Mission queued for {target}: {mission['intent']}",
        level="INFO",
        source=mission["created_by"],
    )
    _save_agents_state(state)

    return jsonify({"ok": True, "mission": mission})


@app.route('/api/missions/update', methods=['POST'])
def api_missions_update():
    """Met a jour le statut d'une mission et l'archive si terminee."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    mission_id = body.get("mission_id", "")
    state = _load_agents_state()
    _ensure_missions(state)
    _ensure_intel(state)
    missions = state["missions"]["active"]
    mission = next((item for item in missions if item.get("mission_id") == mission_id), None)

    if not mission:
        return jsonify({"ok": False, "error": f"Mission {mission_id} inconnue"}), 404

    mission["status"] = body.get("status", mission.get("status", "queued"))
    mission["updated_at"] = _utcnow_iso()
    mission["result"] = body.get("result", mission.get("result"))
    mission["context"] = {**mission.get("context", {}), **body.get("context", {})}

    actor = body.get("actor", mission.get("target", "TRINITY"))
    if actor in state.get("agents", {}):
        state["agents"][actor]["last_seen"] = _utcnow_iso()
        state["agents"][actor]["last_task"] = mission.get("intent")

    if mission["status"] in {"done", "completed", "failed", "cancelled"}:
        _archive_mission(state, mission)

    _record_comet_intel(
        state,
        summary=f"Mission {mission_id} -> {mission['status']}",
        level="INFO" if mission["status"] in {"done", "completed"} else "WARNING",
        source=actor,
    )
    _save_agents_state(state)

    return jsonify({"ok": True, "mission": mission})


@app.route('/api/comet/feed', methods=['GET'])
def api_comet_feed():
    """Retourne le feed COMET/intel conserve en memoire partagee."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    state = _load_agents_state()
    _ensure_intel(state)
    feed = state["intel"].get("comet_feed", [])
    n = int(request.args.get("n", 20))
    return jsonify({"ok": True, "feed": feed[:n], "count": len(feed)})


@app.route('/api/router/report', methods=['GET'])
def api_router_report():
    """Rapport simplifie du routage — pas de GOUV4 dans le cockpit root."""
    state = _load_agents_state()
    agents = state.get("agents", {})
    available = {k: v.get("status", "unknown") for k, v in agents.items()}
    return jsonify({"ok": True, "router": "basic", "agents": available})


@app.route('/api/router/route', methods=['POST'])
def api_router_route():
    """Recommande un agent pour un type de tache (routing simplifie)."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    TASK_AGENTS = {
        "trading_analysis": "ARKON",
        "market_news": "COMET",
        "code_generation": "MERLIN",
        "strategy_planning": "MERLIN",
        "infra_monitoring": "COMET",
        "automation_yaml": "MERLIN",
        "fallback": "MERLIN",
    }
    body = request.get_json(silent=True) or {}
    task_type = body.get("task_type", "fallback")
    chosen = TASK_AGENTS.get(task_type, "MERLIN")
    return jsonify({"ok": True, "task_type": task_type, "recommended_agent": chosen})


@app.route('/api/signal', methods=['POST'])
def api_signal():
    """
    Reception d'un signal de trading multi-source.
    Poids par source: TRINITY=0.80, MERLIN=0.70, KIMI=0.65, ORACLE=0.60, AGENT_LOOP/ONCHAIN=0.55, COMET=0.50
    Formule: effective_confidence = (confidence * weight) + consensus_bonus
    Seuil arkon_pass: effective_confidence >= 0.60
    """
    SOURCE_WEIGHTS = {
        "TRINITY": 0.80, "MERLIN": 0.70, "KIMI": 0.65,
        "ORACLE": 0.60, "AGENT_LOOP": 0.55, "ONCHAIN": 0.55, "COMET": 0.50,
    }

    body = request.get_json(silent=True) or {}
    action = body.get("action", "HOLD").upper()
    symbol = body.get("symbol", "BTC/USDT")
    confidence = float(body.get("confidence", 0.5))
    price = float(body.get("price", 0.0))
    reason = body.get("reason", "")[:300]
    source = body.get("source", "AGENT")

    state = _load_agents_state()
    _ensure_intel(state)
    pipeline = state.get("pipeline", {})
    ts = _utcnow_iso()

    weight = SOURCE_WEIGHTS.get(source.upper(), 0.55)
    weighted_confidence = round(confidence * weight, 4)

    # Consensus: meme symbole + meme action, source differente
    signals_buffer = pipeline.get("signals_buffer", [])
    signals_buffer = [s for s in signals_buffer if s.get("ts", "1970") >= ts[:10]]
    consensus_sources = [
        s for s in signals_buffer
        if s.get("symbol") == symbol
        and s.get("action") == action
        and s.get("source", "").upper() != source.upper()
    ]
    consensus = len(consensus_sources) >= 1
    consensus_bonus = 0.15 if consensus else 0.0
    effective_confidence = round(weighted_confidence + consensus_bonus, 4)

    kill_switch = pipeline.get("kill_switch", False)
    threat_level = pipeline.get("threat_level", "T0")
    mode = pipeline.get("mode", "dry_run")

    arkon_pass = effective_confidence >= 0.60
    risk_pass = arkon_pass and not kill_switch and threat_level in ("T0", "T1")
    verdict = ("EXECUTE" if mode == "authorized" else "SIMULATE_EXECUTE") if risk_pass else "NO_TRADE"

    signals_buffer.append({"symbol": symbol, "action": action, "source": source, "confidence": confidence, "ts": ts})
    pipeline["signals_buffer"] = signals_buffer[-20:]
    pipeline["last_signal"] = {
        "symbol": symbol, "action": action, "confidence": confidence,
        "weight": weight, "weighted_confidence": weighted_confidence,
        "consensus": consensus, "consensus_bonus": consensus_bonus,
        "effective_confidence": effective_confidence,
        "price": price, "reason": reason, "source": source,
        "verdict": verdict, "ts": ts,
    }
    state["pipeline"] = pipeline

    agent_key = source.upper()
    if agent_key in state.get("agents", {}):
        state["agents"][agent_key]["last_seen"] = ts

    _record_comet_intel(
        state,
        summary=f"Signal {source}: {symbol} {action} conf={confidence:.2f} w={weight} eff={effective_confidence:.2f} -> {verdict}",
        level="INFO" if verdict != "NO_TRADE" else "WARNING",
        source=source,
    )
    _save_agents_state(state)

    return jsonify({
        "ok": True, "mode": mode, "symbol": symbol, "action": action, "verdict": verdict,
        "pipeline": {
            "kill_switch": kill_switch, "threat_level": threat_level,
            "confidence": confidence, "weight": weight,
            "weighted_confidence": weighted_confidence, "consensus": consensus,
            "effective_confidence": effective_confidence,
            "arkon_pass": arkon_pass, "risk_pass": risk_pass,
        },
        "ts": ts,
    })


@app.route('/api/intel', methods=['POST'])
def api_intel():
    """Recoit un rapport intel d'un agent (COMET, ARKON, etc.)."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    agent = body.get("agent", "UNKNOWN").upper()
    report = body.get("report", "")
    level = body.get("level", "info")

    state = _load_agents_state()
    _ensure_intel(state)
    _record_comet_intel(state, summary=report, level=level.upper(), source=agent)
    _save_agents_state(state)

    return jsonify({"ok": True, "agent": agent, "received": True})




@app.route('/api/jarvis', methods=['POST'])
def api_jarvis():
    """Proxy chat vers Jarvis (OpenJarvis) via Bras-Alien."""
    body = request.get_json(silent=True) or {}
    message = body.get("message", "")
    if not message:
        return jsonify({"ok": False, "error": "No message"}), 400

    system_prompt = (
        "Tu es Jarvis, assistant IA du systeme S25 Lumiere. "
        "Tu connais les agents: MERLIN (orchestrateur), COMET (watchman), "
        "ARKON-5 (trading signals), KIMI (DEX sniper), TRINITY (voice/proxy), "
        "GEMINI_OPS (health checks), ORACLE, ONCHAIN_GUARDIAN, etc. "
        "Tu tournes sur AlienStef (RTX 3060, Qwen 14b). "
        "Reponds en francais, sois concis et utile."
    )

    try:
        resp = requests.post(
            "http://localhost:3002/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer s25-jarvis-internal-key",
            },
            json={
                "model": "qwen2.5-coder:14b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                "max_tokens": 500,
            },
            timeout=60,
        )
        data = resp.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "...")
        return jsonify({"ok": True, "reply": reply})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502

# ════════════════════════════════════════════════════════════════
# CONTROL LINK — Claude ↔ Trinity validated action chain
# propose → validate → execute (canonical, auditable)
# ════════════════════════════════════════════════════════════════
import uuid

@app.route('/api/control/propose', methods=['POST'])
def api_control_propose():
    body = request.get_json(silent=True) or {}
    action_id = f"ctrl_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    proposal = {
        "action_id": action_id,
        "source": body.get("source", "UNKNOWN"),
        "action_type": body.get("action_type", "custom"),
        "params": body.get("params", {}),
        "reason": body.get("reason", "")[:500],
        "status": "proposed",
        "proposed_at": datetime.now(timezone.utc).isoformat(),
        "validated_at": None, "executed_at": None, "result": None,
    }
    state = _load_agents_state()
    state.setdefault("control_queue", []).append(proposal)
    state["control_queue"] = state["control_queue"][-50:]
    _save_agents_state(state)
    return jsonify({"ok": True, "action_id": action_id, "proposal": proposal})


@app.route('/api/control/validate', methods=['POST'])
def api_control_validate():
    body = request.get_json(silent=True) or {}
    action_id = body.get("action_id", "")
    state = _load_agents_state()
    for item in state.get("control_queue", []):
        if item["action_id"] == action_id and item["status"] == "proposed":
            item["status"] = "validated"
            item["validated_at"] = datetime.now(timezone.utc).isoformat()
            item["validated_by"] = body.get("validator", "OPERATOR")
            _save_agents_state(state)
            return jsonify({"ok": True, "action_id": action_id, "status": "validated"})
    return jsonify({"ok": False, "error": f"Action {action_id} not found or not proposed"}), 404


@app.route('/api/control/execute', methods=['POST'])
def api_control_execute():
    body = request.get_json(silent=True) or {}
    action_id = body.get("action_id", "")
    state = _load_agents_state()
    target = None
    for item in state.get("control_queue", []):
        if item["action_id"] == action_id and item["status"] == "validated":
            target = item
            break
    if not target:
        return jsonify({"ok": False, "error": f"Action {action_id} not validated"}), 404

    params = target.get("params", {})
    result = {"executed": False}
    atype = target["action_type"]

    if atype == "pipeline_mode":
        pipeline = state.setdefault("pipeline", {})
        for k in ("mode", "threat_level", "kill_switch"):
            if k in params:
                pipeline[k] = params[k]
        result = {"executed": True, "detail": f"pipeline: {params}"}
    elif atype == "config_change":
        key, value = params.get("key", ""), params.get("value")
        if key and value is not None:
            state.setdefault("runtime_config", {})[key] = value
            result = {"executed": True, "detail": f"{key}={value}"}
    elif atype == "agent_restart":
        result = {"executed": True, "detail": f"restart queued for {params.get('agent','')}"}
    else:
        result = {"executed": True, "detail": f"custom action logged: {atype}"}

    target["status"] = "executed"
    target["executed_at"] = datetime.now(timezone.utc).isoformat()
    target["result"] = result
    _save_agents_state(state)
    return jsonify({"ok": True, "action_id": action_id, "result": result})


@app.route('/api/control/queue', methods=['GET'])
def api_control_queue():
    state = _load_agents_state()
    queue = state.get("control_queue", [])
    sf = request.args.get("status")
    if sf:
        queue = [q for q in queue if q["status"] == sf]
    return jsonify({"ok": True, "queue": queue, "count": len(queue)})


if __name__ == '__main__':
    port = int(os.getenv("PORT", "7777"))
    app.run(host='0.0.0.0', port=port, debug=False)
