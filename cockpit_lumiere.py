#!/usr/bin/env python3
# ============================================================
# S25 LUMIÈRE — Cockpit Web UI v1.0
# Interface visuelle futuriste pour CentOS Akash
# Accessible via navigateur Web depuis le S25 Ultra
# PORT: 7777
# ============================================================

from flask import Flask, render_template_string, jsonify, request
import os, json, time, requests, subprocess, uuid
from datetime import datetime, timezone
from pathlib import Path
from security.vault import vault_get
from agents.ha_bridge import ha as ha_bridge
from agents.s25_conversation_agent import handle_chat_completion, list_models as list_agent_models, push_mesh_to_ha
from agents.ops_routes import ops_bp
from agents.command_mesh import mesh_bp as command_mesh_bp

MEMORY_DIR = Path(os.getenv("MEMORY_DIR", os.path.expanduser("~/S25-COMMAND-CENTER/memory")))
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SHARED_MEMORY_FILE = MEMORY_DIR / "SHARED_MEMORY.md"
AGENTS_STATE_FILE  = MEMORY_DIR / "agents_state.json"

app = Flask(__name__)
app.register_blueprint(ops_bp)
app.register_blueprint(command_mesh_bp)
_START_TIME = time.time()
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
<title>S25 LUMIERE - COMMAND CENTER</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:radial-gradient(ellipse at top,#0d1b2a 0%,#0a0a0f 100%);color:#e0e6ff;font-family:'Courier New',monospace;min-height:100vh;overflow-x:hidden}
.scanlines{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,200,.015) 2px,rgba(0,255,200,.015) 4px);pointer-events:none;z-index:1}
.wrap{max-width:1600px;margin:0 auto;padding:10px;position:relative;z-index:2}

/* Header */
.hdr{text-align:center;margin-bottom:12px}
.hdr h1{font-size:2rem;color:#00ffcc;text-shadow:0 0 20px #00ffcc,0 0 40px #00ffcc;animation:pulse 2s ease-in-out infinite;letter-spacing:.3em}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.8}}
.hdr .sub{color:#4fc3f7;font-size:.75rem;letter-spacing:.2em;margin-top:2px}
.hdr .clock{color:#888;font-size:.7rem;margin-top:4px}

/* SSE indicator */
.sse-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-left:8px;vertical-align:middle;transition:all .3s}
.sse-dot.on{background:#00ff88;box-shadow:0 0 6px #00ff88}
.sse-dot.off{background:#ff4444;box-shadow:0 0 6px #ff4444}

/* Links bar */
.links{text-align:center;margin-bottom:12px;display:flex;flex-wrap:wrap;justify-content:center;gap:6px}
.links a{color:#4fc3f7;text-decoration:none;font-size:.65rem;padding:3px 8px;border:1px solid rgba(79,195,247,.2);border-radius:3px;transition:all .2s}
.links a:hover{background:rgba(79,195,247,.1);border-color:#4fc3f7}

/* 6-panel grid */
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px}
@media(max-width:900px){.grid{grid-template-columns:1fr}}

/* Panel base */
.panel{background:rgba(13,27,42,.85);border:1px solid rgba(0,255,204,.15);border-radius:6px;padding:10px;min-height:280px;display:flex;flex-direction:column;transition:border-color .3s}
.panel:hover{border-color:rgba(0,255,204,.4)}
.panel-title{font-size:.7rem;color:#00ffcc;letter-spacing:.15em;margin-bottom:8px;text-transform:uppercase;display:flex;justify-content:space-between;align-items:center}
.panel-title .badge{font-size:.6rem;padding:1px 6px;border-radius:3px;background:rgba(0,255,136,.15);color:#00ff88}

/* Agent dots */
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px;vertical-align:middle}
.dot.on{background:#00ff88;box-shadow:0 0 4px #00ff88}
.dot.standby{background:#ff9800;box-shadow:0 0 4px #ff9800}
.dot.off{background:#ff4444;box-shadow:0 0 4px #ff4444}

/* Agent grid */
.ag-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:4px;flex:1;overflow-y:auto}
.ag{background:rgba(0,0,0,.3);border:1px solid rgba(0,255,136,.1);border-radius:4px;padding:5px 6px;font-size:.6rem;transition:border-color .3s}
.ag.on{border-color:rgba(0,255,136,.3)}
.ag.standby{border-color:rgba(255,152,0,.2)}
.ag .name{color:#4fc3f7;font-weight:bold;font-size:.65rem}
.ag .seen{color:#555;font-size:.55rem;margin-top:1px}

/* Signal panel */
.signal-action{font-size:2.5rem;font-weight:bold;text-align:center;margin:8px 0;letter-spacing:.1em}
.signal-action.BUY{color:#00ff88;text-shadow:0 0 20px rgba(0,255,136,.5)}
.signal-action.SELL{color:#ff4444;text-shadow:0 0 20px rgba(255,68,68,.5)}
.signal-action.HOLD{color:#ff9800;text-shadow:0 0 20px rgba(255,152,0,.5)}

/* Confidence gauge */
.gauge{width:100%;height:18px;background:rgba(0,0,0,.4);border-radius:9px;overflow:hidden;margin:6px 0}
.gauge-fill{height:100%;border-radius:9px;transition:width .5s ease,background .5s;display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:bold;color:#000}
.gauge-fill.high{background:linear-gradient(90deg,#00cc66,#00ff88)}
.gauge-fill.mid{background:linear-gradient(90deg,#ff9800,#ffb74d)}
.gauge-fill.low{background:linear-gradient(90deg,#ff4444,#ff6666)}

/* Signal meta */
.sig-meta{font-size:.6rem;color:#888;line-height:1.6}
.sig-meta span{color:#4fc3f7}
.sig-verdict{text-align:center;font-size:.75rem;padding:3px 8px;border-radius:3px;margin:4px 0;font-weight:bold}
.sig-verdict.EXECUTE{background:rgba(0,255,136,.15);color:#00ff88;border:1px solid rgba(0,255,136,.3)}
.sig-verdict.NO_TRADE{background:rgba(255,152,0,.1);color:#ff9800;border:1px solid rgba(255,152,0,.2)}

/* Agent team cards */
.team-grid{display:flex;flex-direction:column;gap:4px;flex:1;overflow-y:auto}
.team-card{display:flex;align-items:center;gap:8px;background:rgba(0,0,0,.3);border:1px solid rgba(79,195,247,.1);border-radius:4px;padding:6px 8px;transition:border-color .3s}
.team-card:hover{border-color:rgba(79,195,247,.4)}
.team-icon{font-size:1.1rem}
.team-info{flex:1}
.team-name{font-size:.65rem;color:#4fc3f7;font-weight:bold}
.team-role{font-size:.55rem;color:#888}
.team-status{font-size:.55rem;color:#555}

/* Intel feed */
.intel-feed{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:2px;max-height:250px}
.intel-item{font-size:.58rem;padding:3px 6px;border-left:2px solid #4fc3f7;background:rgba(0,0,0,.2);line-height:1.4}
.intel-item.INFO{border-color:#00ffcc}
.intel-item.WARNING{border-color:#ff9800}
.intel-item.ERROR{border-color:#ff4444}
.intel-item.CRITICAL{border-color:#ff0000;background:rgba(255,0,0,.05)}
.intel-src{color:#4fc3f7;font-weight:bold;font-size:.55rem}
.intel-time{color:#555;font-size:.5rem;float:right}

/* Control queue */
.ctrl-queue{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:4px}
.ctrl-item{background:rgba(0,0,0,.3);border-radius:4px;padding:6px;font-size:.6rem;border-left:3px solid #ff9800}
.ctrl-item.proposed{border-color:#ff9800}
.ctrl-item.validated{border-color:#4fc3f7}
.ctrl-item.executed{border-color:#00ff88}
.ctrl-type{font-weight:bold;color:#4fc3f7}
.ctrl-btns{display:flex;gap:4px;margin-top:4px}

/* Jarvis chat */
.j-msgs{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:3px;max-height:220px;padding:4px}
.j-msg{font-size:.6rem;padding:4px 6px;border-radius:4px;line-height:1.4;max-width:90%}
.j-msg.user{background:rgba(79,195,247,.1);align-self:flex-end;border:1px solid rgba(79,195,247,.2)}
.j-msg.ai{background:rgba(0,255,204,.05);align-self:flex-start;border:1px solid rgba(0,255,204,.1)}
.j-input{display:flex;gap:4px;margin-top:6px}
.j-input input{flex:1;background:rgba(0,0,0,.4);border:1px solid rgba(79,195,247,.2);color:#e0e6ff;padding:6px 8px;border-radius:4px;font-family:inherit;font-size:.65rem;outline:none}
.j-input input:focus{border-color:#4fc3f7}
.j-input input::placeholder{color:#555}

/* Buttons */
.btn{padding:4px 10px;border:1px solid rgba(0,255,204,.3);background:rgba(0,255,204,.05);color:#00ffcc;border-radius:3px;cursor:pointer;font-family:inherit;font-size:.6rem;transition:all .2s}
.btn:hover{background:rgba(0,255,204,.15);border-color:#00ffcc}
.btn.danger{border-color:rgba(255,68,68,.3);color:#ff4444;background:rgba(255,68,68,.05)}
.btn.danger:hover{background:rgba(255,68,68,.15)}
.btn.primary{border-color:rgba(79,195,247,.3);color:#4fc3f7;background:rgba(79,195,247,.05)}
.btn.sm{padding:2px 6px;font-size:.55rem}

/* Footer */
.foot{text-align:center;color:#333;font-size:.55rem;margin-top:8px;letter-spacing:.1em}

/* Scrollbar */
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(0,255,204,.2);border-radius:2px}
::-webkit-scrollbar-thumb:hover{background:rgba(0,255,204,.4)}
</style>
</head>
<body>
<div class="scanlines"></div>
<div class="wrap">

<!-- HEADER -->
<div class="hdr">
  <h1>S25 LUMIERE</h1>
  <div class="sub">COMMAND CENTER // AlienStef Node <span class="sse-dot off" id="sse-dot" title="SSE"></span></div>
  <div class="clock" id="clock"></div>
</div>

<!-- LINKS -->
<div class="links">
  <a href="https://alien.smajor.org" target="_blank">Open WebUI</a>
  <a href="https://jarvis.smajor.org/docs" target="_blank">Jarvis API</a>
  <a href="https://api-alien.smajor.org" target="_blank">Bras-Alien</a>
  <a href="https://cockpit-alien.smajor.org" target="_blank">Cockpit</a>
  <a href="https://smajor.org" target="_blank">smajor.org</a>
  <a href="https://app.smajor.org" target="_blank">Admin</a>
  <a href="/api/trading/overview" target="_blank">Trading API</a>
  <a href="/api/ha/status" target="_blank">HA Status</a>
</div>

<!-- 6-PANEL GRID -->
<div class="grid">

  <!-- P1: MESH COMMAND -->
  <div class="panel" id="p-mesh">
    <div class="panel-title">MESH COMMAND <span class="badge" id="mesh-count">--/--</span></div>
    <div class="ag-grid" id="mesh-agents"></div>
    <div style="margin-top:6px;display:flex;gap:4px">
      <button class="btn sm" onclick="wakeAgents()">WAKE ALL</button>
      <button class="btn sm primary" onclick="refreshAll()">REFRESH</button>
      <span id="missions-count" style="color:#888;font-size:.55rem;line-height:2"></span>
    </div>
  </div>

  <!-- P2: SIGNAL PIPELINE -->
  <div class="panel" id="p-signal">
    <div class="panel-title">SIGNAL PIPELINE <span class="badge" id="sig-mode">--</span></div>
    <div class="signal-action HOLD" id="sig-action">--</div>
    <div class="gauge"><div class="gauge-fill mid" id="sig-gauge" style="width:0%">0%</div></div>
    <div class="sig-verdict NO_TRADE" id="sig-verdict">WAITING</div>
    <div class="sig-meta">
      Symbol: <span id="sig-symbol">--</span> | Price: <span id="sig-price">--</span><br>
      Source: <span id="sig-source">--</span> | Consensus: <span id="sig-consensus">--</span><br>
      Weight: <span id="sig-weight">--</span> | Effective: <span id="sig-eff">--</span>
    </div>
    <div style="margin-top:auto;display:flex;gap:4px">
      <button class="btn danger sm" onclick="toggleKill()">KILL SWITCH</button>
      <span id="kill-status" style="color:#00ff88;font-size:.55rem;line-height:2">OFF</span>
    </div>
  </div>

  <!-- P3: AGENT TEAM -->
  <div class="panel" id="p-team">
    <div class="panel-title">AGENT TEAM <span class="badge" id="team-count">0 active</span></div>
    <div class="team-grid" id="team-grid">
      <div class="team-card"><span class="team-icon">C</span><div class="team-info"><div class="team-name">Claude / ARKON</div><div class="team-role">Trading Analysis + Code</div><div class="team-status" id="t-arkon">--</div></div><span class="dot off" id="td-arkon"></span></div>
      <div class="team-card"><span class="team-icon">G</span><div class="team-info"><div class="team-name">GPT / TRINITY</div><div class="team-role">Strategy Planning</div><div class="team-status" id="t-trinity">--</div></div><span class="dot off" id="td-trinity"></span></div>
      <div class="team-card"><span class="team-icon">P</span><div class="team-info"><div class="team-name">Perplexity / COMET</div><div class="team-role">Market Research</div><div class="team-status" id="t-comet">--</div></div><span class="dot off" id="td-comet"></span></div>
      <div class="team-card"><span class="team-icon">M</span><div class="team-info"><div class="team-name">Gemini / MERLIN</div><div class="team-role">Risk Assessment</div><div class="team-status" id="t-merlin">--</div></div><span class="dot off" id="td-merlin"></span></div>
      <div class="team-card"><span class="team-icon">K</span><div class="team-info"><div class="team-name">Kimi / KIMI</div><div class="team-role">DEX Sniper</div><div class="team-status" id="t-kimi">--</div></div><span class="dot off" id="td-kimi"></span></div>
      <div class="team-card"><span class="team-icon">O</span><div class="team-info"><div class="team-name">Oracle / ORACLE</div><div class="team-role">Price Feed</div><div class="team-status" id="t-oracle">--</div></div><span class="dot off" id="td-oracle"></span></div>
    </div>
  </div>

  <!-- P4: INTEL FEED -->
  <div class="panel" id="p-intel">
    <div class="panel-title">INTEL FEED <span class="badge" id="intel-count">0</span></div>
    <div class="intel-feed" id="intel-feed"></div>
  </div>

  <!-- P5: CONTROL LINK -->
  <div class="panel" id="p-control">
    <div class="panel-title">CONTROL LINK <span class="badge" id="ctrl-count">0 pending</span></div>
    <div class="ctrl-queue" id="ctrl-queue"></div>
    <div style="margin-top:auto;display:flex;gap:4px;flex-wrap:wrap">
      <button class="btn sm primary" onclick="dispatchTask('market_research','Analyze current market conditions')">Research</button>
      <button class="btn sm primary" onclick="dispatchTask('risk_assessment','Evaluate portfolio risk')">Risk</button>
      <button class="btn sm primary" onclick="dispatchTask('trading_analysis','Generate trading signal')">Analyze</button>
      <button class="btn sm" onclick="dispatchTask('infra_monitoring','System health check')">Infra</button>
    </div>
  </div>

  <!-- P6: JARVIS CHAT -->
  <div class="panel" id="p-jarvis">
    <div class="panel-title">JARVIS <span style="font-size:.55rem;color:#555">slash: /status /signal /dispatch /wake /kill</span></div>
    <div class="j-msgs" id="j-msgs"></div>
    <div class="j-input">
      <input id="j-in" placeholder="Message ou /commande..." onkeydown="if(event.key==='Enter')sendJ()">
      <button class="btn sm" onclick="sendJ()">SEND</button>
    </div>
  </div>

</div><!-- grid -->

<div class="foot">S25 LUMIERE v3.0 // AlienStef + Cloudflare + Home Assistant // <span id="uptime">--</span></div>
</div><!-- wrap -->

<script>
const SECRET = '';
const headers = {'Content-Type':'application/json'};

// === SSE ===
let sse = null;
function connectSSE() {
  if (sse) sse.close();
  sse = new EventSource('/api/stream');
  sse.onopen = () => { document.getElementById('sse-dot').className = 'sse-dot on'; };
  sse.onerror = () => { document.getElementById('sse-dot').className = 'sse-dot off'; };
  sse.addEventListener('mesh_update', e => { const d = JSON.parse(e.data); updateMesh(d); });
  sse.addEventListener('signal', e => { const d = JSON.parse(e.data); updateSignal(d); });
  sse.addEventListener('intel', e => { const d = JSON.parse(e.data); addIntel(d); });
  sse.addEventListener('control_update', e => { const d = JSON.parse(e.data); updateControl(d); });
  sse.addEventListener('heartbeat', e => {});
  sse.onmessage = e => {};
}

// === CLOCK ===
setInterval(() => {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleDateString('fr-CA') + ' ' + now.toLocaleTimeString('fr-CA');
}, 1000);

// === MESH ===
function updateMesh(data) {
  const mesh = data.mesh || data;
  const agents = mesh.agents || {};
  const el = document.getElementById('mesh-agents');
  document.getElementById('mesh-count').textContent = (mesh.online||0) + '/' + (mesh.total_agents||Object.keys(agents).length);
  document.getElementById('missions-count').textContent = (mesh.missions_active||0) + ' missions';
  let html = '';
  for (const [name, info] of Object.entries(agents).sort()) {
    const st = info.status || 'off';
    const cls = st === 'online' ? 'on' : st === 'standby' ? 'standby' : 'off';
    const seen = info.last_seen ? timeAgo(info.last_seen) : '--';
    html += '<div class="ag '+cls+'"><span class="dot '+cls+'"></span><span class="name">'+name+'</span><div class="seen">'+seen+'</div></div>';
  }
  el.innerHTML = html;
  // Update team dots
  const teamMap = {ARKON: 'arkon', 'ARKON-5': 'arkon', TRINITY: 'trinity', COMET: 'comet', MERLIN: 'merlin', KIMI: 'kimi', ORACLE: 'oracle'};
  let activeCount = 0;
  for (const [agent, id] of Object.entries(teamMap)) {
    const a = agents[agent];
    const dot = document.getElementById('td-'+id);
    const txt = document.getElementById('t-'+id);
    if (a && dot) {
      const st = a.status || 'off';
      dot.className = 'dot ' + (st==='online'?'on':st==='standby'?'standby':'off');
      txt.textContent = st + ' | ' + (a.last_seen ? timeAgo(a.last_seen) : '--');
      if (st === 'online') activeCount++;
    }
  }
  document.getElementById('team-count').textContent = activeCount + ' active';
}

// === SIGNAL ===
function updateSignal(data) {
  const sig = data.last_signal || data;
  const action = sig.action || 'HOLD';
  const el = document.getElementById('sig-action');
  el.textContent = action;
  el.className = 'signal-action ' + action;

  const eff = sig.effective_confidence || 0;
  const pct = Math.round(eff * 100);
  const gauge = document.getElementById('sig-gauge');
  gauge.style.width = pct + '%';
  gauge.textContent = pct + '%';
  gauge.className = 'gauge-fill ' + (pct >= 65 ? 'high' : pct >= 45 ? 'mid' : 'low');

  const verdict = sig.verdict || 'NO_TRADE';
  const vEl = document.getElementById('sig-verdict');
  vEl.textContent = verdict;
  vEl.className = 'sig-verdict ' + (verdict.includes('EXECUTE') ? 'EXECUTE' : 'NO_TRADE');

  document.getElementById('sig-symbol').textContent = sig.symbol || '--';
  document.getElementById('sig-price').textContent = sig.price ? '$'+Number(sig.price).toLocaleString() : '--';
  document.getElementById('sig-source').textContent = sig.source || '--';
  document.getElementById('sig-consensus').textContent = sig.consensus ? 'YES' : 'NO';
  document.getElementById('sig-weight').textContent = sig.weight || '--';
  document.getElementById('sig-eff').textContent = eff ? eff.toFixed(3) : '--';
  document.getElementById('sig-mode').textContent = data.mode || sig.mode || '--';
}

// === INTEL ===
function addIntel(item) {
  const feed = document.getElementById('intel-feed');
  const level = item.level || 'INFO';
  const div = document.createElement('div');
  div.className = 'intel-item ' + level;
  const ts = item.ts ? item.ts.substring(11, 19) : '';
  div.innerHTML = '<span class="intel-src">' + (item.source||'') + '</span> <span class="intel-time">' + ts + '</span><br>' + (item.summary||item.message||'');
  feed.insertBefore(div, feed.firstChild);
  while (feed.children.length > 50) feed.removeChild(feed.lastChild);
  document.getElementById('intel-count').textContent = feed.children.length;
}

// === CONTROL ===
function updateControl(data) {
  const queue = data.queue || data.proposals || [];
  const el = document.getElementById('ctrl-queue');
  const pending = queue.filter(i => i.status === 'proposed').length;
  document.getElementById('ctrl-count').textContent = pending + ' pending';
  let html = '';
  for (const item of queue.slice(-10).reverse()) {
    const cls = item.status || 'proposed';
    html += '<div class="ctrl-item '+cls+'">';
    html += '<span class="ctrl-type">' + (item.action_type||item.type||'task') + '</span> ';
    html += '<span style="color:#888">' + (item.source||'') + '</span><br>';
    html += (item.reason||item.description||'').substring(0, 120);
    if (cls === 'proposed') {
      html += '<div class="ctrl-btns"><button class="btn sm" onclick="validateCtrl(\''+item.action_id+'\')">Validate</button><button class="btn sm primary" onclick="executeCtrl(\''+item.action_id+'\')">Execute</button></div>';
    }
    html += '</div>';
  }
  el.innerHTML = html || '<div style="color:#555;font-size:.6rem;text-align:center;padding:20px">No pending proposals</div>';
}

// === JARVIS ===
const jMsgs = [];
function sendJ() {
  const input = document.getElementById('j-in');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  // Slash commands
  if (msg.startsWith('/')) {
    handleSlash(msg);
    return;
  }

  addJMsg('user', msg);
  fetch('/api/jarvis', {method:'POST', headers, body:JSON.stringify({message:msg})})
    .then(r=>r.json())
    .then(d=>{ addJMsg('ai', d.reply || d.response || JSON.stringify(d)); })
    .catch(e=>{ addJMsg('ai', 'Error: '+e.message); });
}

function addJMsg(role, text) {
  const el = document.getElementById('j-msgs');
  const div = document.createElement('div');
  div.className = 'j-msg ' + role;
  div.textContent = text;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

async function handleSlash(cmd) {
  const parts = cmd.split(/\s+/);
  const slash = parts[0].toLowerCase();
  addJMsg('user', cmd);

  if (slash === '/status') {
    const r = await fetch('/api/mesh/status').then(r=>r.json());
    addJMsg('ai', 'Mesh: '+r.mesh.online+'/'+r.mesh.total_agents+' | Missions: '+r.mesh.missions_active+' | Intel: '+r.mesh.intel_entries);
  } else if (slash === '/overview') {
    const r = await fetch('/api/trading/overview').then(r=>r.json());
    const t = r.trading;
    addJMsg('ai', 'Pipeline: '+t.pipeline.mode+' | Kill: '+(t.pipeline.kill_switch?'ON':'OFF')+' | MEXC: '+(t.cex.mexc.configured?'OK':'NO')+' | DEX: '+(t.dex.uniswap_arb?.web3_connected?'OK':'NO'));
  } else if (slash === '/wake') {
    const r = await fetch('/api/ha/agents/wake',{method:'POST',headers}).then(r=>r.json());
    addJMsg('ai', 'Woken: '+r.woken.join(', '));
  } else if (slash === '/signal' && parts.length >= 3) {
    const body = {action:parts[1],symbol:parts[2],confidence:parseFloat(parts[3]||'0.7'),source:'JARVIS'};
    const r = await fetch('/api/signal',{method:'POST',headers,body:JSON.stringify(body)}).then(r=>r.json());
    addJMsg('ai', r.verdict+' | eff='+r.pipeline.effective_confidence);
  } else if (slash === '/kill') {
    addJMsg('ai', 'Kill switch toggled (use HA for safety)');
  } else if (slash === '/dispatch' && parts.length >= 2) {
    const task = parts[1];
    const intent = parts.slice(2).join(' ') || task;
    const r = await fetch('/api/orchestrator/dispatch',{method:'POST',headers,body:JSON.stringify({task_type:task,intent:intent})}).then(r=>r.json());
    addJMsg('ai', 'Dispatched to: '+(r.agent||'--')+' | Status: '+(r.status||'queued'));
  } else if (slash === '/ha') {
    const r = await fetch('/api/ha/status').then(r=>r.json());
    const agents = Object.entries(r.ha.agents).filter(([k,v])=>v==='active').map(([k])=>k);
    addJMsg('ai', 'HA Agents active: '+agents.join(', ')+' | Kill: '+r.ha.controls.s25_kill_switch);
  } else {
    addJMsg('ai', 'Commands: /status /overview /wake /signal ACTION SYMBOL CONF /dispatch TYPE INTENT /ha /kill');
  }
}

// === ACTIONS ===
async function wakeAgents() {
  const r = await fetch('/api/ha/agents/wake',{method:'POST',headers}).then(r=>r.json());
  addJMsg('ai', 'Agents woken: ' + (r.woken||[]).join(', '));
  refreshAll();
}

async function toggleKill() {
  addJMsg('ai', 'Kill switch — use HA dashboard for safety toggle');
}

async function dispatchTask(type, intent) {
  const r = await fetch('/api/orchestrator/dispatch',{method:'POST',headers,body:JSON.stringify({task_type:type,intent:intent})}).then(r=>r.json());
  addJMsg('ai', 'Dispatched '+type+' -> '+(r.agent||'queued'));
  refreshAll();
}

async function validateCtrl(id) {
  await fetch('/api/control/validate',{method:'POST',headers,body:JSON.stringify({action_id:id})});
  refreshAll();
}

async function executeCtrl(id) {
  await fetch('/api/control/execute',{method:'POST',headers,body:JSON.stringify({action_id:id})});
  refreshAll();
}

// === REFRESH ===
async function refreshAll() {
  try {
    const [mesh, overview, intel, ctrl] = await Promise.all([
      fetch('/api/mesh/status').then(r=>r.json()),
      fetch('/api/trading/overview').then(r=>r.json()),
      fetch('/api/intel?n=30').then(r=>r.json()),
      fetch('/api/control/queue').then(r=>r.json()),
    ]);
    updateMesh(mesh);
    if (overview.trading) {
      updateSignal({...overview.trading.pipeline, last_signal: overview.trading.pipeline.last_signal});
    }
    if (intel.feed) {
      document.getElementById('intel-feed').innerHTML = '';
      intel.feed.slice(0, 30).reverse().forEach(i => addIntel(i));
    }
    updateControl(ctrl);
  } catch(e) { console.error('Refresh error:', e); }
}

// === UTILS ===
function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return Math.round(diff) + 's';
  if (diff < 3600) return Math.round(diff/60) + 'm';
  if (diff < 86400) return Math.round(diff/3600) + 'h';
  return Math.round(diff/86400) + 'd';
}

// === INIT ===
connectSSE();
refreshAll();
setInterval(refreshAll, 60000);
</script>
</body>
</html>

'''


def _ha_kill_switch_active(timeout: float = 2.0) -> bool:
    """Read input_boolean.s25_kill_switch from HA. Returns True if ON."""
    try:
        ha_url = (vault_get("HA_URL", os.getenv("HA_URL", "http://homeassistant.local:8123")) or "").rstrip("/")
        ha_token = vault_get("HA_TOKEN", os.getenv("HA_TOKEN", ""))
        if not ha_token:
            return False
        r = requests.get(
            f"{ha_url}/api/states/input_boolean.s25_kill_switch",
            headers={"Authorization": f"Bearer {ha_token}"},
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json().get("state") == "on"
    except Exception:
        pass
    return False


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

    if not ha_bridge.connected:
        return jsonify(status)

    try:
        entity_map = {
            "sensor.s25_arkon5_action": "arkon5_action",
            "sensor.s25_arkon5_conf": "arkon5_conf",
            "input_text.ai_model_actif": "pipeline_status",
            "sensor.antminer_hashrate": "hashrate",
            "sensor.antminer_temp": "temp",
            "input_text.s25_comet_intel": "comet_intel",
        }
        for entity, key in entity_map.items():
            data = ha_bridge.get_state(entity)
            if data:
                status[key] = data.get("state", "--")

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

    if action == 'start_tunnel':
        subprocess.Popen(["bash", "/config/scripts/start_s25_tunnel.sh"])
        return jsonify({"ok": True, "msg": "Tunnel démarré"})

    elif action == 'stop_tunnel':
        subprocess.run(["pkill", "-f", "cloudflared"])
        return jsonify({"ok": True, "msg": "Tunnel arrêté"})

    elif action == 'force_analysis':
        ha_bridge.call_service("automation", "trigger",
                              {"entity_id": "automation.s25_arkon5_buy_alert"})
        return jsonify({"ok": True, "msg": "Analyse déclenchée"})

    elif action == 'purge':
        ha_bridge.call_service("input_boolean", "turn_on",
                              {"entity_id": "input_boolean.s25_kill_switch"})
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


@app.route('/openapi.yaml', methods=['GET'])
@app.route('/openapi.json', methods=['GET'])
def serve_openapi():
    """Public OpenAPI schema for Trinity Custom GPT import (no auth)."""
    try:
        import yaml, json as _j
        from pathlib import Path as _P
        p = _P(__file__).parent / "trinity_config" / "openapi_trinity.yaml"
        if not p.exists():
            p = _P(__file__).parent / "agents" / "trinity_gpt_config" / "openapi_spec.yaml"
        if not p.exists():
            return jsonify({"ok": False, "error": "openapi file not found"}), 404
        raw = p.read_text()
        # Serve as YAML if extension requested, JSON otherwise
        if request.path.endswith(".json"):
            data = yaml.safe_load(raw)
            resp = app.response_class(_j.dumps(data, indent=2), mimetype='application/json')
        else:
            resp = app.response_class(raw, mimetype='application/yaml')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Cache-Control'] = 'public, max-age=300'
        return resp
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


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
    """MERLIN — local-only mode since 2026-04-22 (Google AI Studio retired).
    For intelligent responses, Major uses Gemini Pro web manually."""
    return (
        "MERLIN local-mode: Google AI Studio retired (403 DENIED). "        "For deep analysis, use Gemini Pro web. This bridge returns market snapshot only."    )
    # ---- legacy code below kept but never reached ----
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
    # SSE: broadcast state changes to connected dashboards
    try:
        agents = state.get("agents", {})
        _broadcast("mesh_update", {"mesh": {
            "agents": {k: {"status": v.get("status"), "last_seen": v.get("last_seen")} for k, v in agents.items()},
            "online": sum(1 for a in agents.values() if a.get("status") == "online"),
            "total_agents": len(agents),
            "missions_active": len(state.get("missions", {}).get("active", [])),
        }})
        ls = state.get("pipeline", {}).get("last_signal")
        if ls:
            _broadcast("signal", {**ls, "mode": state.get("pipeline", {}).get("mode", "dry_run")})
    except Exception:
        pass


@app.route('/mcp', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/mcp/<path:subpath>', methods=['GET', 'POST', 'OPTIONS'])
def mcp_proxy(subpath=''):
    """Reverse-proxy /mcp* to local merlin_mcp_bridge on 127.0.0.1:8000.

    Keeps merlin.smajor.org/mcp live via cockpit-alien.smajor.org tunnel
    until Akash merlin-mesh is redeployed.
    """
    from flask import Response
    target = 'http://127.0.0.1:8000/mcp'
    if subpath:
        target += '/' + subpath
    qs = request.query_string.decode() if request.query_string else ''
    if qs:
        target += '?' + qs
    excluded = {'host', 'connection', 'content-length'}
    fwd_headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded}
    try:
        upstream = requests.request(
            method=request.method,
            url=target,
            headers=fwd_headers,
            data=request.get_data() if request.method not in ('GET', 'HEAD') else None,
            stream=True,
            timeout=60,
            allow_redirects=False,
        )
    except Exception as e:
        return jsonify({'ok': False, 'error': 'merlin_unreachable', 'detail': str(e)}), 502
    drop = {'connection', 'transfer-encoding', 'content-encoding', 'content-length'}
    resp_headers = [(k, v) for k, v in upstream.headers.items() if k.lower() not in drop]
    def generate():
        for chunk in upstream.iter_content(chunk_size=4096):
            if chunk:
                yield chunk
    return Response(generate(), status=upstream.status_code, headers=resp_headers)


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
    """Ensure state has intel/comet_feed structure. Migrates legacy list format."""
    intel = state.get("intel")
    if not isinstance(intel, dict):
        # Legacy: intel was a flat list — migrate to dict with comet_feed
        legacy_entries = intel if isinstance(intel, list) else []
        state["intel"] = {"comet_feed": legacy_entries[-50:]}
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
    # SSE: broadcast intel entry to connected dashboards
    try:
        _broadcast("intel", entry)
    except Exception:
        pass
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
    Phase 2 backpressure (Trinity §22 Test 3):
      when stability_layer reports congested, normal+low priority signals → 429.
      Critical and high always pass.
    """
    # Backpressure throttle (Phase 2)
    try:
        _body_peek = request.get_json(silent=True) or {}
    except Exception:
        _body_peek = {}
    try:
        from agents.stability_layer import should_throttle, backpressure_level
        _prio = str(_body_peek.get('priority') or 'normal').lower()
        _throttle, _reason = should_throttle(_prio)
        if _throttle:
            _bp = backpressure_level()
            resp = jsonify({
                'ok': False,
                'throttled': True,
                'reason': _reason,
                'backpressure': _bp,
                'priority': _prio,
                'retry_after_sec': 5,
            })
            resp.status_code = 429
            resp.headers['Retry-After'] = '5'
            return resp
    except Exception as _e:
        # Never block ingest if stability layer unavailable
        pass
    SOURCE_WEIGHTS = {
        "TRINITY": 0.80, "TRADINGVIEW": 0.85, "MERLIN": 0.70, "KIMI": 0.65,
        "ORACLE": 0.60, "AGENT_LOOP": 0.55, "ONCHAIN": 0.55, "COMET": 0.50,
        "ARKON5": 0.75, "ARKON": 0.75, "MESH_BRIDGE": 0.70, "AUTO_SCANNER": 0.70,
        "TV_PINE": 0.80,
    }

    body = request.get_json(silent=True) or {}
    # If no JSON body, try to parse text/plain Pine alert_message
    if not body:
        try:
            raw = request.get_data(as_text=True) or ""
            if raw.strip():
                import json as _rjson
                try:
                    body = _rjson.loads(raw)
                except Exception:
                    up = raw.strip().upper()
                    parsed = {}
                    if any(t in up for t in ("BUY","LONG","STRONGBUY")):
                        parsed["action"] = "BUY"
                    elif any(t in up for t in ("SELL","SHORT","EXIT","CLOSE","STRONGSELL")):
                        parsed["action"] = "SELL"
                    for tok in up.replace("/", " ").replace("-", " ").split():
                        if "USD" in tok and tok not in ("USDC", "USDT", "USD"):
                            parsed["symbol"] = tok
                            break
                    parsed["source"] = "TRADINGVIEW"
                    parsed["reason"] = raw[:200]
                    body = parsed
        except Exception:
            body = {}

    # ── 3-min dedup cooldown (source|norm_symbol|action) ──
    # Multiple agents (oracle, merlin, commander, mesh_bridge) publish the same
    # ARKON5 state within a few seconds. Without this, each publish spams HA
    # notifications + signals_buffer + CEX attempts. Cooldown dedups at the
    # very entry point, so downstream (notif, buffer, cex) all skip.
    try:
        _early_source = str(body.get("source", "") or "AGENT").upper()
        _early_symbol = str(body.get("symbol", "") or "BTC/USDT").upper().replace("/", "").replace("-", "")
        for _q in ("USDT", "USDC"):
            if _early_symbol.endswith(_q):
                _early_symbol = _early_symbol[:-len(_q)] + "USD"
                break
        _early_action = str(body.get("action", "") or "HOLD").upper()
        import json as _ejson, time as _etime
        from pathlib import Path as _ePath
        _cd_path = _ePath("memory") / "api_signal_entry_cooldown.json"
        _cd_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _cd = _ejson.loads(_cd_path.read_text()) if _cd_path.exists() else {}
        except Exception:
            _cd = {}
        _cd_key = f"{_early_source}|{_early_symbol}|{_early_action}"
        _cd_now = _etime.time()
        _cd_last = float(_cd.get(_cd_key, 0))
        ENTRY_COOLDOWN_SEC = 180  # 3 minutes
        if _cd_now - _cd_last < ENTRY_COOLDOWN_SEC and _early_action in ("BUY", "SELL"):
            return jsonify({
                "ok": True,
                "skipped": "entry_cooldown",
                "key": _cd_key,
                "age_sec": int(_cd_now - _cd_last),
                "message": "deduplicated — same signal within 3min",
            })
        _cd[_cd_key] = _cd_now
        _cd = {k: v for k, v in _cd.items() if _cd_now - float(v) < 1800}  # prune 30min+
        _cd_path.write_text(_ejson.dumps(_cd, indent=2))
    except Exception as _ecd_e:
        pass  # fail-open: never block on cooldown bugs

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

    kill_switch = pipeline.get("kill_switch", False) or _ha_kill_switch_active()
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

    # Push signal to Home Assistant (sensors + MEXC execution)
    ha_result = None
    try:
        ha_result = _ha_push_signal(action, symbol, confidence, effective_confidence, price, reason, verdict, source)
    except Exception as _ha_err:
        ha_result = {"ok": False, "error": str(_ha_err)}

    # === Coinbase CEX execution (Phase 7b) — fires on EXECUTE verdict ===
    # Cooldown 5 min per (source, symbol, action) to prevent multi-daemon
    # spam (oracle + merlin + commander all publish same ARKON5 signal
    # every 1-2 min; without this, each one fires a Coinbase order).
    cex_result_from_api_signal = None
    if verdict == "EXECUTE" and action in ("BUY", "SELL"):
        try:
            import json as _cbjson
            from pathlib import Path as _cbPath
            import time as _cbtime
            _cb_cd_path = _cbPath("memory") / "api_signal_cex_cooldown.json"
            _cb_cd_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                _cb_cd = _cbjson.loads(_cb_cd_path.read_text()) if _cb_cd_path.exists() else {}
            except Exception:
                _cb_cd = {}
            # Normalize symbol so BTC/USDT, BTC/USD, BTCUSD, BTC-USD all share the same cooldown slot
            _cb_norm_sym = symbol.upper().replace("/","").replace("-","")
            for _q in ("USDT","USDC"):
                if _cb_norm_sym.endswith(_q):
                    _cb_norm_sym = _cb_norm_sym[:-len(_q)] + "USD"
                    break
            _cb_key = f"{source}|{_cb_norm_sym}|{action}".upper()
            _cb_now = _cbtime.time()
            _cb_last = float(_cb_cd.get(_cb_key, 0))
            COOLDOWN_SEC = 5 * 60
            if _cb_now - _cb_last < COOLDOWN_SEC:
                cex_result_from_api_signal = {
                    "ok": False,
                    "skipped": "cooldown",
                    "key": _cb_key,
                    "age_sec": int(_cb_now - _cb_last),
                }
            else:
                _cb_cd[_cb_key] = _cb_now
                # prune old keys
                _cb_cd = {k: v for k, v in _cb_cd.items() if _cb_now - float(v) < 3600}
                _cb_cd_path.write_text(_cbjson.dumps(_cb_cd, indent=2))

                from agents.coinbase_executor import get_executor as _cb_get
                _cbx = _cb_get()
                cex_result_from_api_signal = _cbx.execute_signal({
                    "action": action,
                    "symbol": symbol,
                    "source": source,
                    "reason": reason or f"api_signal {source}",
                })
        except Exception as _cbe:
            cex_result_from_api_signal = {"error": str(_cbe)}

    return jsonify({
        "ok": True, "mode": mode, "symbol": symbol, "action": action, "verdict": verdict,
        "cex_result": cex_result_from_api_signal,
        "ha_bridge": ha_result,
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



# ═══════════════════════════════════════════════════════════════
#  WALLET STATUS — Treasury balances via on-chain queries
# ═══════════════════════════════════════════════════════════════


# ---------------------------------------------------------------------------
# Creator-route: unified wallet mnemonic source status (safe, no value leak)
# ---------------------------------------------------------------------------
@app.route("/api/wallet/creator/status", methods=["GET"])
def api_wallet_creator_status():
    try:
        from security.wallet_creator import status as _wc_status, _ALIASES
        st = _wc_status()
        st["aliases_checked"] = list(_ALIASES)
        return jsonify({"ok": True, **st})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/wallet/status", methods=["GET"])
def api_wallet_status():
    """Retourne les balances wallet on-chain (ATOM, AKT, Akash escrow)."""
    AKASH_LCD = "https://rest.cosmos.directory/akash"
    COSMOS_LCD = "https://rest.cosmos.directory/cosmoshub"
    AKASH_WALLET = os.getenv("AKASH_WALLET_ADDRESS", "")

    result = {
        "ok": True,
        "ts": _utcnow_iso(),
        "wallets": {},
        "prices": {},
    }

    # Prices
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "akash-network,cosmos", "vs_currencies": "usd"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            result["prices"]["AKT"] = data.get("akash-network", {}).get("usd", 0)
            result["prices"]["ATOM"] = data.get("cosmos", {}).get("usd", 0)
    except Exception:
        pass

    akt_price = result["prices"].get("AKT", 0)
    atom_price = result["prices"].get("ATOM", 0)

    # AKT balance
    if AKASH_WALLET:
        try:
            r = requests.get(
                f"{AKASH_LCD}/cosmos/bank/v1beta1/balances/{AKASH_WALLET}",
                timeout=10,
            )
            if r.status_code == 200:
                for b in r.json().get("balances", []):
                    if b["denom"] in ("uakt", "uact"):
                        amt = int(b["amount"]) / 1_000_000
                        result["wallets"]["AKT"] = {
                            "address": AKASH_WALLET,
                            "balance": round(amt, 6),
                            "usd": round(amt * akt_price, 2),
                        }
        except Exception:
            pass

    # ATOM balance (derive cosmos address from env if available)
    cosmos_addr = os.getenv("COSMOS_WALLET_ADDRESS", "")
    if cosmos_addr:
        try:
            r = requests.get(
                f"{COSMOS_LCD}/cosmos/bank/v1beta1/balances/{cosmos_addr}",
                timeout=10,
            )
            if r.status_code == 200:
                for b in r.json().get("balances", []):
                    if b["denom"] == "uatom":
                        amt = int(b["amount"]) / 1_000_000
                        result["wallets"]["ATOM"] = {
                            "address": cosmos_addr,
                            "balance": round(amt, 6),
                            "usd": round(amt * atom_price, 2),
                        }
        except Exception:
            pass

    # Total USD
    total_usd = sum(w.get("usd", 0) for w in result["wallets"].values())
    result["total_usd"] = round(total_usd, 2)

    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
#  GET /api/signal — Read signal history from pipeline buffer
# ═══════════════════════════════════════════════════════════════

@app.route("/api/signal", methods=["GET"])
def api_signal_get():
    """Retourne l historique des signaux et le dernier signal du pipeline."""
    state = _load_agents_state()
    pipeline = state.get("pipeline", {})
    return jsonify({
        "ok": True,
        "last_signal": pipeline.get("last_signal"),
        "signals_buffer": pipeline.get("signals_buffer", []),
        "source_weights": pipeline.get("source_weights", {}),
        "mode": pipeline.get("mode", "dry_run"),
        "kill_switch": pipeline.get("kill_switch", False),
        "threat_level": pipeline.get("threat_level", "T0"),
    })


# ═══════════════════════════════════════════════════════════════
#  GET /api/intel — Read intel/comet feed history
# ═══════════════════════════════════════════════════════════════

@app.route("/api/intel", methods=["GET"])
def api_intel_get():
    """Retourne le feed intel complet (comet_feed)."""
    state = _load_agents_state()
    _ensure_intel(state)
    feed = state["intel"].get("comet_feed", [])
    n = int(request.args.get("n", 50))
    level = request.args.get("level", "").upper()
    source = request.args.get("source", "").upper()
    if level:
        feed = [e for e in feed if e.get("level") == level]
    if source:
        feed = [e for e in feed if e.get("source") == source]
    return jsonify({"ok": True, "feed": feed[:n], "count": len(feed)})





# ═══════════════════════════════════════════════════════════════
#  S25 LUMIERE — Trading Routes Extension
#  Webhook receivers + DEX execution + Multi-chain status
#  Injected into cockpit_lumiere.py before __main__
# ═══════════════════════════════════════════════════════════════


@app.route('/webhook/tv_pine', methods=['POST'])
def webhook_tv_pine():
    """Polymorphic TradingView / Pine-script / legacy Kimi webhook receiver.

    Accepts any of these body formats:
      - Native TradingView alert: {"ticker":"BTCUSD","action":"buy","price":...}
      - Pine strategy: {"strategy.order.action":"buy","strategy.order.contracts":0.01,
                        "ticker":"{{ticker}}","close":"{{close}}"}
      - Legacy Kimi: {"symbol":"BTC/USDT","side":"BUY","confidence":0.82,...}
      - Merlin/Perplexity bridged: {"scan_data":{...}}
      - Plain text body: "BUY BTCUSD" (parsed line)

    Normalizes and forwards to the existing /webhook/tradingview pipeline
    so risk/kill-switch/bracket/trailing all apply uniformly.
    """
    try:
        raw = request.get_data(as_text=True) or ""
        # Try JSON first
        import json as _json
        body = {}
        try:
            body = _json.loads(raw) if raw.strip().startswith(("{", "[")) else {}
        except Exception:
            body = {}

        # Nested Kimi-style scan_data
        if isinstance(body, dict) and isinstance(body.get("scan_data"), dict):
            body = {**body, **body["scan_data"]}

        # Extract fields with many aliases
        ticker = (body.get("ticker") or body.get("symbol")
                  or body.get("pair") or body.get("asset") or "").upper()
        ticker = ticker.replace("/", "").replace("-", "")
        # Accept Pine {{ticker}}
        if ticker.startswith("{{") and ticker.endswith("}}"):
            ticker = ""

        action_raw = str(
            body.get("action")
            or body.get("side")
            or body.get("order_action")
            or body.get("strategy.order.action")
            or ""
        ).upper()
        if action_raw in ("LONG", "BUY", "STRONGBUY"):
            action = "BUY"
        elif action_raw in ("SHORT", "SELL", "EXIT", "CLOSE", "STRONGSELL"):
            action = "SELL"
        elif action_raw == "HOLD":
            action = "HOLD"
        else:
            action = ""

        # Parse plain text if JSON failed
        if not (ticker and action) and raw:
            parts = raw.strip().upper().split()
            if len(parts) >= 2:
                for tok in parts:
                    if tok in ("BUY", "SELL", "LONG", "SHORT"):
                        action = "BUY" if tok in ("BUY", "LONG") else "SELL"
                    elif "USD" in tok or "USDT" in tok:
                        ticker = tok.replace("/", "").replace("-", "")

        if not ticker or not action:
            return jsonify({"ok": False, "error": "missing_ticker_or_action",
                            "raw_received": raw[:300]}), 400

        price = float(
            body.get("price")
            or body.get("close")
            or body.get("entry")
            or 0
        )
        confidence = float(body.get("confidence") or body.get("conf") or 0.75)
        usd_amount = body.get("usd_amount") or body.get("quantity_usd") or body.get("size_usd")
        strategy_name = str(
            body.get("strategy")
            or body.get("strategy.name")
            or body.get("pine_name")
            or "tv_pine_relay"
        )
        source = (body.get("source") or "TRADINGVIEW").upper()

        # Forward to the canonical webhook with the proper passphrase so it's
        # auth'd, and we reuse all the risk/execution plumbing.
        tv_pp = vault_get("TV_PASSPHRASE", os.getenv("TV_PASSPHRASE", "")) or ""
        forward_body = {
            "ticker": ticker,
            "action": action,
            "price": price,
            "confidence": confidence,
            "strategy": f"[tv_pine] {strategy_name}",
            "source": source,
            "passphrase": tv_pp,
        }
        if usd_amount is not None:
            try:
                forward_body["usd_amount"] = float(usd_amount)
            except Exception:
                pass

        # Call our own webhook (internal, no auth roundtrip)
        import requests as _req
        r = _req.post("http://localhost:7777/webhook/tradingview",
                      json=forward_body, timeout=10)
        out = r.json() if r.headers.get("Content-Type","").startswith("application/json") else {"raw": r.text[:500]}
        return jsonify({"ok": True, "relayed": forward_body, "pipeline_response": out}), r.status_code
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/webhook/tradingview', methods=['POST'])
def webhook_tradingview():
    """
    Receive TradingView alerts and inject into signal pipeline.
    JSON: {ticker, action, price, passphrase, [interval, strategy, confidence]}
    """
    TV_PASSPHRASE = vault_get("TV_PASSPHRASE", os.getenv("TV_PASSPHRASE", ""))
    body = request.get_json(force=True, silent=True) or {}

    if TV_PASSPHRASE and body.get("passphrase") != TV_PASSPHRASE:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    ticker = body.get("ticker", body.get("symbol", "")).upper()
    action = body.get("action", body.get("order_action", "HOLD")).upper()
    price = float(body.get("price", body.get("close", 0)))
    interval = body.get("interval", "")
    strategy = body.get("strategy", body.get("strategy_name", ""))
    confidence = float(body.get("confidence", 0.75))

    action_map = {"BUY": "BUY", "SELL": "SELL", "LONG": "BUY", "SHORT": "SELL",
                  "STRONGBUY": "BUY", "STRONGSELL": "SELL", "EXIT": "SELL",
                  "CLOSE": "SELL", "HOLD": "HOLD"}
    normalized_action = action_map.get(action, "HOLD")

    symbol = ticker
    for quote in ["USDT", "USDC", "USD", "BUSD"]:
        if ticker.endswith(quote) and "/" not in ticker:
            symbol = ticker[:-len(quote)] + "/" + quote
            break

    reason = f"TradingView: {strategy} on {interval}" if strategy else f"TradingView {action} alert"

    ts = datetime.now(timezone.utc).isoformat()
    state = _load_agents_state()
    _ensure_intel(state)
    pipeline = state.get("pipeline", {})

    TV_WEIGHTS = {
        "TRINITY": 0.80, "TRADINGVIEW": 0.85, "MERLIN": 0.70, "KIMI": 0.65,
        "ORACLE": 0.60, "AGENT_LOOP": 0.55, "ONCHAIN": 0.55, "COMET": 0.50,
        "ARKON5": 0.75, "ARKON": 0.75, "MESH_BRIDGE": 0.70, "AUTO_SCANNER": 0.70,
    }
    # Body can override source so mesh-driven signals (TRINITY, ARKON5, MERLIN, ...)
    # keep their weight instead of being treated as plain TradingView alerts.
    bridge_source = str(body.get("source", "") or "").upper() or "TRADINGVIEW"
    weight = TV_WEIGHTS.get(bridge_source, 0.75)
    weighted_confidence = round(confidence * weight, 4)

    signals_buffer = pipeline.get("signals_buffer", [])
    signals_buffer = [s for s in signals_buffer if s.get("ts", "1970") >= ts[:10]]
    consensus_sources = [
        s for s in signals_buffer
        if s.get("symbol") == symbol and s.get("action") == normalized_action
        and s.get("source", "").upper() != "TRADINGVIEW"
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

    signals_buffer.append({"symbol": symbol, "action": normalized_action, "source": bridge_source,
                          "confidence": confidence, "ts": ts, "strategy": strategy, "interval": interval})
    pipeline["signals_buffer"] = signals_buffer[-20:]
    pipeline["last_signal"] = {
        "symbol": symbol, "action": normalized_action, "confidence": confidence,
        "weight": weight, "weighted_confidence": weighted_confidence,
        "consensus": consensus, "consensus_bonus": consensus_bonus,
        "effective_confidence": effective_confidence,
        "price": price, "reason": reason, "source": bridge_source,
        "verdict": verdict, "ts": ts,
    }
    state["pipeline"] = pipeline

    _record_comet_intel(
        state,
        summary=f"TRADINGVIEW: {symbol} {normalized_action} @{price} conf={confidence:.2f} eff={effective_confidence:.2f} -> {verdict}",
        level="INFO" if verdict != "NO_TRADE" else "WARNING",
        source="TRADINGVIEW",
    )
    _save_agents_state(state)

    # Push TradingView signal to Home Assistant
    ha_result = None
    try:
        ha_result = _ha_push_signal(normalized_action, symbol, confidence, effective_confidence, price, reason, verdict, bridge_source)
    except Exception as _ha_err:
        ha_result = {"ok": False, "error": str(_ha_err)}

    dex_result = None
    if verdict == "EXECUTE" and normalized_action in ("BUY", "SELL"):
        try:
            from agents.uniswap_executor import get_executor
            exe = get_executor()
            token_in = "USDC" if normalized_action == "BUY" else "WETH"
            token_out = "WETH" if normalized_action == "BUY" else "USDC"
            dex_result = exe.execute_swap(token_in, token_out, exe.max_trade_usd,
                                         reason=reason, source=bridge_source)
        except Exception as e:
            dex_result = {"error": str(e)}

    # --- Coinbase Advanced branch (dry-run safe, gated by HA kill-switch already checked) ---
    cex_result = None
    if verdict == "EXECUTE" and normalized_action in ("BUY", "SELL"):
        try:
            from agents.coinbase_executor import get_executor as _cb_get
            cbx = _cb_get()
            cex_result = cbx.execute_signal({
                "action": normalized_action,
                "symbol": symbol,
                "source": bridge_source,
                "reason": reason,
                "usd_amount": float(body.get("usd_amount", cbx.max_usd_per_trade)),
            })
        except Exception as _cbe:
            cex_result = {"error": str(_cbe)}

    return jsonify({
        "cex_result": cex_result,
        "ok": True, "source": bridge_source, "symbol": symbol,
        "action": normalized_action, "price": price, "verdict": verdict,
        "pipeline": {
            "confidence": confidence, "weight": weight,
            "weighted_confidence": weighted_confidence,
            "consensus": consensus, "effective_confidence": effective_confidence,
            "arkon_pass": arkon_pass, "risk_pass": risk_pass,
            "mode": mode, "kill_switch": kill_switch,
        },
        "dex_execution": dex_result,
        "ts": ts,
    })


# ═══════════════════════════════════════════════════════════════
#  POST /api/dex/swap — Direct DEX swap execution
# ═══════════════════════════════════════════════════════════════

@app.route('/api/dex/swap', methods=['POST'])
def api_dex_swap():
    """Execute a DEX swap via Uniswap V3 on Arbitrum."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    token_in = body.get("token_in", "USDC")
    token_out = body.get("token_out", "WETH")
    amount_usd = float(body.get("amount_usd", 0))
    reason = body.get("reason", "manual swap")

    try:
        from agents.uniswap_executor import get_executor
        exe = get_executor()
        result = exe.execute_swap(token_in, token_out, amount_usd, reason=reason, source="COCKPIT")

        state = _load_agents_state()
        _ensure_intel(state)
        _record_comet_intel(state,
            summary=f"DEX SWAP: ${amount_usd} {token_in}->{token_out} [{result.get('status')}]",
            level="INFO", source="DEX_EXECUTOR")
        _save_agents_state(state)

        return jsonify({"ok": True, "swap": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
#  GET /api/dex/status — DEX executor status + wallet
# ═══════════════════════════════════════════════════════════════

@app.route('/api/dex/status', methods=['GET'])
def api_dex_status():
    """Uniswap executor status, wallet balance, trade count."""
    try:
        from agents.uniswap_executor import get_executor
        exe = get_executor()
        return jsonify({"ok": True, "dex": exe.get_status()})
    except Exception as e:
        return jsonify({"ok": True, "dex": {"mode": "not_loaded", "error": str(e)}})


# ═══════════════════════════════════════════════════════════════
#  GET /api/dex/price — Uniswap price quote
# ═══════════════════════════════════════════════════════════════

@app.route('/api/dex/price', methods=['GET'])
def api_dex_price():
    """Get price quote from Uniswap V3."""
    token_in = request.args.get("token_in", "WETH")
    token_out = request.args.get("token_out", "USDC")
    try:
        from agents.uniswap_executor import get_executor
        exe = get_executor()
        return jsonify({"ok": True, "price": exe.get_price(token_in, token_out)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
#  GET /api/dex/trades — Trade ledger history
# ═══════════════════════════════════════════════════════════════

@app.route('/api/dex/trades', methods=['GET'])
def api_dex_trades():
    """DEX trade history from ledger."""
    try:
        from agents.uniswap_executor import get_executor
        exe = get_executor()
        ledger = exe._load_ledger()
        n = int(request.args.get("n", 50))
        return jsonify({"ok": True, "trades": ledger[-n:], "total": len(ledger)})
    except Exception as e:
        return jsonify({"ok": True, "trades": [], "error": str(e)})


# ═══════════════════════════════════════════════════════════════
#  POST /api/treasury/autorefuel — ATOM->AKT swap + ghost cleanup
# ═══════════════════════════════════════════════════════════════

@app.route('/api/treasury/autorefuel', methods=['POST', 'GET'])
def api_treasury_autorefuel():
    """Run the treasury autorefuel orchestrator (ATOM->AKT + akash cleanup).

    Query/JSON params:
      dry_run       1 to plan only (default 1 for GET, 0 for POST)
      atom_amount   ATOM to swap if refuel triggered (default 1.0)
      min_uakt      threshold below which to refuel (default 1500000)
      no_swap       1 to skip swap step
      no_cleanup    1 to skip cleanup step
    """
    import subprocess as _sp
    params = request.get_json(silent=True) or {}
    if request.args:
        params = {**params, **request.args.to_dict()}
    default_dry = "0" if request.method == "POST" else "1"
    env = {
        **os.environ,
        "DRY_RUN": str(params.get("dry_run", default_dry)),
        "REFUEL_ATOM": str(params.get("atom_amount", "1.0")),
        "MIN_UAKT": str(params.get("min_uakt", "1500000")),
        "NO_SWAP": str(params.get("no_swap", "0")),
        "NO_CLEANUP": str(params.get("no_cleanup", "0")),
    }
    script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "tools", "treasury_autorefuel.py",
    )
    try:
        proc = _sp.run(
            ["python3", script],
            env=env, capture_output=True, text=True, timeout=900,
        )
        return jsonify({
            "ok": proc.returncode == 0,
            "rc": proc.returncode,
            "stdout": proc.stdout[-8000:],
            "stderr": proc.stderr[-2000:],
            "params": {
                "dry_run": env["DRY_RUN"],
                "atom_amount": env["REFUEL_ATOM"],
                "min_uakt": env["MIN_UAKT"],
                "no_swap": env["NO_SWAP"],
                "no_cleanup": env["NO_CLEANUP"],
            },
        }), 200 if proc.returncode == 0 else 500
    except _sp.TimeoutExpired:
        return jsonify({"ok": False, "error": "timeout after 900s"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
#  GET /api/trading/overview — Unified multi-chain trading dashboard
# ═══════════════════════════════════════════════════════════════


@app.route('/api/coinbase/portfolio', methods=['GET'])
def api_coinbase_portfolio():
    try:
        from agents.coinbase_executor import get_executor
        return jsonify(get_executor().get_portfolio())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/coinbase/payment-methods', methods=['GET'])
def api_coinbase_payment_methods():
    try:
        from agents.coinbase_executor import get_executor
        return jsonify(get_executor().get_payment_methods())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/coinbase/fee-tier', methods=['GET'])
def api_coinbase_fee_tier():
    try:
        from agents.coinbase_executor import get_executor
        return jsonify(get_executor().get_fee_tier())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/coinbase/preview', methods=['POST'])
def api_coinbase_preview():
    try:
        body = request.get_json(force=True, silent=True) or {}
        product_id = str(body.get("product_id", "BTC-USD")).upper()
        side = str(body.get("side", "BUY")).upper()
        usd_amount = float(body.get("usd_amount", 10.0))
        from agents.coinbase_executor import get_executor
        return jsonify(get_executor().preview_order(product_id, side, usd_amount))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/positions', methods=['GET'])
def api_trading_positions():
    """Open positions + realized P&L snapshot."""
    try:
        from agents.position_tracker import compute_positions
        from agents.coinbase_executor import get_executor
        exe = get_executor()
        result = compute_positions(spot_fn=exe.get_product_price)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/strategies', methods=['GET'])
def api_trading_strategies():
    """List all strategies with their enabled status + last signal info."""
    try:
        import strategies
        reg = strategies.bootstrap()
        return jsonify({"ok": True, "strategies": reg.snapshot()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/strategies/<name>/toggle', methods=['POST', 'GET'])
def api_strategy_toggle(name):
    """Enable/disable a strategy. POST {enabled:bool} or GET ?enabled=true|false"""
    try:
        import strategies
        reg = strategies.bootstrap()
        if request.method == 'GET':
            qp = request.args.get('enabled')
            if qp is None:
                return jsonify({"ok": False, "error": "pass ?enabled=true|false"}), 400
            new_state = qp.strip().lower() in ('true', '1', 'yes', 'on')
        else:
            body = request.get_json(force=True, silent=True) or {}
            new_state = bool(body.get('enabled', False))
        if not reg.toggle(name, new_state):
            return jsonify({"ok": False, "error": f"unknown strategy: {name}"}), 404
        return jsonify({"ok": True, "strategy": name, "enabled": new_state})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/strategies/<name>/symbols', methods=['POST'])
def api_strategy_symbols(name):
    try:
        import strategies
        reg = strategies.bootstrap()
        body = request.get_json(force=True, silent=True) or {}
        symbols = body.get('symbols', [])
        if not reg.set_symbols(name, symbols):
            return jsonify({'ok': False, 'error': f'unknown strategy: {name}'}), 404
        return jsonify({'ok': True, 'strategy': name, 'symbols': reg.get_symbols(name)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/trading/strategies/<name>/usd-size', methods=['POST'])
def api_strategy_usd_size(name):
    """Set per-strategy USD notional. POST {usd: float}"""
    try:
        import strategies
        reg = strategies.bootstrap()
        body = request.get_json(force=True, silent=True) or {}
        usd = float(body.get('usd', 0))
        if usd <= 0:
            return jsonify({"ok": False, "error": "usd must be > 0"}), 400
        if not reg.set_usd_size(name, usd):
            return jsonify({"ok": False, "error": f"unknown strategy: {name}"}), 404
        return jsonify({"ok": True, "strategy": name, "usd_size": usd})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/backtest', methods=['POST', 'GET'])
def api_trading_backtest():
    """Run a strategy backtest on Coinbase historical candles.
    POST {strategy, symbol, days} | GET ?strategy=&symbol=&days="""
    try:
        from agents.backtester import run_all
        if request.method == 'POST':
            body = request.get_json(force=True, silent=True) or {}
        else:
            body = {
                "strategy": request.args.get("strategy"),
                "symbol": request.args.get("symbol"),
                "days": request.args.get("days", 12),
            }
        strategy = body.get("strategy")
        symbol = body.get("symbol")
        days = int(body.get("days", 12))
        if not strategy or not symbol:
            return jsonify({"ok": False, "error": "strategy and symbol are required"}), 400
        return jsonify(run_all(strategy, symbol, days=days))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/backtest/all', methods=['GET'])
def api_trading_backtest_all():
    """Backtest every strategy on every whitelist coin. Return a matrix."""
    try:
        from agents.backtester import run_all
        from agents.coinbase_executor import get_executor
        import strategies
        reg = strategies.bootstrap()
        exe = get_executor()
        symbols = sorted(exe.allowed_products)
        days = int(request.args.get("days", 12))
        results = []
        for strat_name in reg.strategies.keys():
            for symbol in symbols:
                r = run_all(strat_name, symbol, days=days)
                if r.get("ok"):
                    results.append({
                        "strategy": strat_name, "symbol": symbol,
                        "trades": r.get("trades", 0),
                        "win_rate_pct": r.get("win_rate_pct", 0),
                        "total_pnl_pct": r.get("total_pnl_pct", 0),
                        "max_dd_pct": r.get("max_drawdown_pct", 0),
                    })
        return jsonify({"ok": True, "days": days, "matrix": results})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/dca', methods=['GET', 'POST', 'DELETE'])
def api_trading_dca():
    """DCA schedules management.
    GET  -> list with next-fire times
    POST {name, symbol, usd, interval_hours}  -> add/update
    DELETE ?name=  -> remove"""
    try:
        from agents.dca_scheduler import list_schedules, add_schedule, load_schedules, save_schedules
        if request.method == 'GET':
            return jsonify({"ok": True, "schedules": list_schedules()})
        if request.method == 'POST':
            body = request.get_json(force=True, silent=True) or {}
            r = add_schedule(body)
            return jsonify({"ok": True, "schedule": r})
        if request.method == 'DELETE':
            name = request.args.get("name")
            schedules = [s for s in load_schedules() if s.get("name") != name]
            save_schedules(schedules)
            return jsonify({"ok": True, "removed": name})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/risk-config', methods=['GET', 'POST'])
def api_trading_risk_config():
    """Get or update risk engine configuration.
    POST body can update: risk_per_trade_pct, default_sl_pct, default_tp_pct,
                          use_volatility_sl, atr_multiplier, max_concurrent_positions,
                          max_single_trade_usd, trail_activation_pct, trail_step_pct,
                          trail_enabled
    """
    try:
        from agents import risk_engine
        from agents.coinbase_executor import get_executor
        if request.method == 'POST':
            body = request.get_json(force=True, silent=True) or {}
            updated = risk_engine.set_config(body)
            return jsonify({"ok": True, "config": updated})
        exe = get_executor()
        portfolio = exe.get_portfolio_usd()
        candles_by_symbol = {}
        for sym in sorted(exe.allowed_products):
            try:
                candles_by_symbol[sym] = exe.get_candles(sym, "ONE_HOUR", limit=30)
            except Exception:
                candles_by_symbol[sym] = []
        return jsonify({"ok": True, **risk_engine.summary(portfolio, candles_by_symbol)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/trailing/run', methods=['POST', 'GET'])
def api_trading_trailing_run():
    """Manually trigger one trailing-stop tick."""
    try:
        from agents.trailing_stop_manager import run_tick
        return jsonify(run_tick())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/news', methods=['GET'])
def api_trading_news():
    """Latest Perplexity news/sentiment scan."""
    try:
        from pathlib import Path as _P
        import json as _j
        p = _P("memory") / "news_scan.json"
        if not p.exists():
            return jsonify({"ok": False, "error": "no scan yet — need PERPLEXITY_API_KEY + cron tick"}), 404
        return jsonify({"ok": True, **_j.loads(p.read_text())})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/brief', methods=['GET'])
def api_trading_brief():
    """Latest Gemini-generated analyst brief."""
    try:
        from pathlib import Path as _P
        import json as _j
        p = _P("memory") / "gemini_brief.json"
        if not p.exists():
            return jsonify({"ok": False, "error": "no brief yet; wait for next cron tick"}), 404
        return jsonify({"ok": True, **_j.loads(p.read_text())})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/pnl', methods=['GET'])
def api_trading_pnl():
    """Condensed P&L dashboard endpoint."""
    try:
        from agents.position_tracker import compute_positions
        from agents.coinbase_executor import get_executor
        exe = get_executor()
        r = compute_positions(spot_fn=exe.get_product_price)
        return jsonify({
            "ok": True,
            "realized_pnl_total": r.get("realized_pnl_total", 0),
            "unrealized_pnl_total": r.get("unrealized_pnl_total", 0),
            "total_pnl": r.get("total_pnl", 0),
            "win_rate_pct": r.get("win_rate_pct"),
            "realized_trades_count": r.get("realized_pnl_count", 0),
            "open_position_count": r.get("open_position_count", 0),
            "avg_win_usd": r.get("avg_win_usd"),
            "avg_loss_usd": r.get("avg_loss_usd"),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/trade-log', methods=['GET'])
def api_trading_trade_log():
    """Return the last N trades from the append-only JSONL log."""
    try:
        from agents.position_tracker import last_trades
        n = int(request.args.get('n', 20))
        return jsonify({"ok": True, "trades": last_trades(n=n)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/backfill-fills', methods=['POST'])
def api_trading_backfill_fills():
    """Refresh avg_price/fee from Coinbase for trades that were submitted
    before we knew their fill state."""
    try:
        from agents.position_tracker import backfill_fills
        from agents.coinbase_executor import get_executor
        exe = get_executor()
        updated = backfill_fills(exe._get_order_info)
        return jsonify({"ok": True, "updated": updated})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/coinbase/live-mode', methods=['GET', 'POST'])
def api_coinbase_live_mode():
    """Toggle LIVE trading flag for Coinbase executor.

    GET  -> current state
    POST {"enabled": true|false}  -> write the flag and return new state
    """
    try:
        from agents.coinbase_executor import CoinbaseExecutor, get_executor
        import pathlib
        flag = pathlib.Path(CoinbaseExecutor.LIVE_FLAG_PATH)

        if request.method == 'GET':
            # Support URL-triggered flips: /api/coinbase/live-mode?enabled=true|false
            qp = request.args.get('enabled')
            if qp is not None:
                new_state = qp.strip().lower() in ('true', '1', 'yes', 'on')
                result = CoinbaseExecutor.set_live_mode(new_state)
                try:
                    exe = get_executor()
                    exe._ha_mode_ts = 0
                    exe.refresh_mode_from_ha()
                    result["executor_dry_run"] = exe.dry_run
                except Exception:
                    pass
                return jsonify(result)
            enabled = flag.exists() and flag.read_text().strip().lower() == 'on'
            return jsonify({"ok": True, "enabled": enabled, "flag_path": str(flag)})

        body = request.get_json(force=True, silent=True) or {}
        new_state = bool(body.get('enabled', False))
        result = CoinbaseExecutor.set_live_mode(new_state)
        # Force the executor to re-read immediately (invalidate cache)
        try:
            exe = get_executor()
            exe._ha_mode_ts = 0
            exe.refresh_mode_from_ha()
            result["executor_dry_run"] = exe.dry_run
        except Exception:
            pass
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/coinbase/spot-prices', methods=['GET'])
def api_coinbase_spot_prices():
    """Live spot prices for our whitelist."""
    try:
        from agents.coinbase_executor import get_executor
        exe = get_executor()
        prices = {p: exe.get_product_price(p) for p in sorted(exe.allowed_products)}
        return jsonify({"ok": True, "prices": prices, "ts": _utcnow_iso()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/coinbase/status', methods=['GET'])
def api_trading_coinbase_status():
    try:
        from agents.coinbase_executor import get_executor
        return jsonify({"ok": True, **get_executor().exec_status()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/trading/overview', methods=['GET'])
def api_trading_overview():
    """Full trading system overview: pipeline + CEX + DEX + wallets."""
    state = _load_agents_state()
    pipeline = state.get("pipeline", {})

    overview = {
        "pipeline": {
            "mode": pipeline.get("mode", "dry_run"),
            "kill_switch": pipeline.get("kill_switch", False),
            "threat_level": pipeline.get("threat_level", "T0"),
            "last_signal": pipeline.get("last_signal", {}),
            "signals_buffer_count": len(pipeline.get("signals_buffer", [])),
        },
        "cex": {
            "mexc": {
                "configured": bool(vault_get("MEXC_API_KEY", "")),
                "mode": "dry_run",
            },
            "crypto_com": {
                "configured": bool(os.getenv("CDC_API_KEY", vault_get("CDC_API_KEY", ""))),
                "mode": "dry_run",
            },
        },
        "dex": {},
        "webhooks": {
            "tradingview": {
                "endpoint": "/webhook/tradingview",
                "configured": bool(vault_get("TV_PASSPHRASE", os.getenv("TV_PASSPHRASE", ""))),
                "external_url": "https://cockpit-alien.smajor.org/webhook/tradingview",
            },
        },
    }

    try:
        from agents.uniswap_executor import get_executor
        overview["dex"]["uniswap_arb"] = get_executor().get_status()
    except Exception as e:
        overview["dex"]["uniswap_arb"] = {"error": str(e)}

    
    # Coinbase Advanced section (added 2026-04-19)
    coinbase_block = None
    try:
        from agents.coinbase_executor import get_executor as _cb
        _cbx = _cb()
        _cbx.refresh_mode_from_ha()
        coinbase_block = {
            **_cbx.exec_status(),
            'portfolio': _cbx.get_portfolio(),
            'fee_tier': _cbx.get_fee_tier(),
        }
    except Exception as _cbe:
        coinbase_block = {'error': str(_cbe)}

    return jsonify({
        "coinbase": coinbase_block,"ok": True, "trading": overview})






# ═══════════════════════════════════════════════════════════════
#  Crypto.com Exchange endpoints
# ═══════════════════════════════════════════════════════════════

@app.route("/api/cdc/test", methods=["GET"])
def api_cdc_test():
    """Test Crypto.com Exchange API connection."""
    try:
        from agents.cryptocom_executor import CryptocomExecutor
        exe = CryptocomExecutor({})
        result = exe.test_connection()
        return jsonify({"ok": result.get("connected", False), "exchange": "crypto.com", **result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/cdc/balance", methods=["GET"])
def api_cdc_balance():
    """Get Crypto.com Exchange account balance."""
    try:
        from agents.cryptocom_executor import CryptocomExecutor
        exe = CryptocomExecutor({})
        result = exe.get_balance()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════
#  S25 LUMIERE — HA Trading Bridge
#  Pushes signals to Home Assistant sensors + triggers execution
#  Injected into cockpit_lumiere.py
# ═══════════════════════════════════════════════════════════════


def _ha_push_signal(action, symbol, confidence, effective_confidence, price, reason, verdict, source):
    """Push trading signal to HA via centralized ha_bridge module."""
    return ha_bridge.push_signal(action, symbol, confidence, effective_confidence, price, reason, verdict, source)


def _ha_wake_agents():
    """Wake up all standby agents in HA."""
    if not HA_URL or not HA_TOKEN:
        return {"ok": False, "error": "HA not configured"}

    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    agents = ["analyste", "coordinateur", "devops", "recherche", "conversation", "trading"]
    woken = []

    for agent in agents:
        try:
            # Set agent status to active
            entity = f"input_text.agent_{agent}_status"
            requests.post(f"{HA_URL}/api/services/input_text/set_value",
                          headers=headers, json={
                              "entity_id": entity,
                              "value": "active"
                          }, timeout=5)

            # Also update the sensor
            requests.post(f"{HA_URL}/api/states/sensor.agent_{agent}", headers=headers, json={
                "state": "active",
                "attributes": {
                    "friendly_name": f"Agent {agent.capitalize()}",
                    "activated_by": "cockpit_pipeline",
                    "activated_at": datetime.now(timezone.utc).isoformat(),
                }
            }, timeout=5)
            woken.append(agent)
        except Exception as e:
            pass

    # Enable multi-agent system + trading
    try:
        requests.post(f"{HA_URL}/api/services/input_boolean/turn_on",
                      headers=headers, json={"entity_id": "input_boolean.mexc_trading_enabled"}, timeout=5)
        woken.append("mexc_trading_enabled")
    except Exception:
        pass

    return {"ok": True, "woken": woken, "count": len(woken)}


# ═══════════════════════════════════════════════════════════════
#  GET /api/ha/agents/wake — Wake all standby agents
# ═══════════════════════════════════════════════════════════════

@app.route('/api/ha/agents/wake', methods=['POST'])
def api_ha_wake_agents():
    """Wake up all standby HA agents."""
    result = _ha_wake_agents()

    state = _load_agents_state()
    _ensure_intel(state)
    _record_comet_intel(state,
        summary=f"HA AGENTS WOKEN: {', '.join(result.get('woken', []))}",
        level="INFO", source="HA_BRIDGE")
    _save_agents_state(state)

    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
#  GET /api/ha/status — Full HA trading status
# ═══════════════════════════════════════════════════════════════

@app.route('/api/ha/status', methods=['GET'])
def api_ha_status():
    """Return full HA trading status — agents, balances, prices."""
    if not HA_URL or not HA_TOKEN:
        return jsonify({"ok": False, "error": "HA not configured"})

    headers = {"Authorization": f"Bearer {HA_TOKEN}"}
    try:
        resp = requests.get(f"{HA_URL}/api/states", headers=headers, timeout=10)
        states = resp.json()

        ha_status = {
            "agents": {},
            "mexc": {},
            "prices": {},
            "controls": {},
            "notifications": {},
        }

        for s in states:
            e = s.get("entity_id", "")
            st = s.get("state", "")
            attrs = s.get("attributes", {})

            # Agents
            if e.startswith("sensor.agent_") or e.startswith("input_text.agent_"):
                name = e.split("agent_")[-1].replace("_status", "")
                ha_status["agents"][name] = st

            # MEXC
            if "mexc" in e and "sensor." in e:
                key = e.replace("sensor.", "")
                ha_status["mexc"][key] = st

            # Balances
            if e.startswith("input_number.mexc_"):
                key = e.replace("input_number.", "")
                ha_status["mexc"][key] = st

            # Prices
            if "price" in e and "sensor." in e:
                ha_status["prices"][attrs.get("friendly_name", e)] = st

            # Controls
            if e.startswith("input_boolean."):
                ha_status["controls"][e.replace("input_boolean.", "")] = st

        return jsonify({"ok": True, "ha": ha_status})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})




# ═══════════════════════════════════════════════════════════════
#  S25 LUMIERE — SSE Live Stream + Orchestrator Dispatch
#  Phase 1 + 3 + 4 of the Unified Control Center plan
#  Inject into cockpit_lumiere.py before __main__
# ═══════════════════════════════════════════════════════════════

import queue
import threading

# ── SSE Infrastructure ──────────────────────────────────────

_sse_clients = []
_sse_lock = threading.Lock()


def _broadcast(event_type, data):
    """Push an SSE event to all connected clients."""
    msg = json.dumps(data) if not isinstance(data, str) else data
    dead = []
    with _sse_lock:
        for q in _sse_clients:
            try:
                q.put_nowait((event_type, msg))
            except Exception:
                dead.append(q)
        for q in dead:
            _sse_clients.remove(q)


@app.route('/api/stream')
def api_stream():
    """SSE endpoint — real-time events for the dashboard."""
    def generate():
        q = queue.Queue(maxsize=100)
        with _sse_lock:
            _sse_clients.append(q)
        try:
            # Send initial state
            yield f"event: heartbeat\ndata: {json.dumps({'ts': _utcnow_iso()})}\n\n"
            while True:
                try:
                    event_type, data = q.get(timeout=15)
                    yield f"event: {event_type}\ndata: {data}\n\n"
                except queue.Empty:
                    yield f"event: heartbeat\ndata: {json.dumps({'ts': _utcnow_iso()})}\n\n"
        except GeneratorExit:
            pass
        finally:
            with _sse_lock:
                if q in _sse_clients:
                    _sse_clients.remove(q)

    from flask import Response
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no',
                             'Connection': 'keep-alive'})


# ── Orchestrator Dispatch ───────────────────────────────────

ORCHESTRATOR_ROUTES = {
    "trading_analysis": {"agent": "ARKON-5", "model": "Claude", "priority": "high"},
    "market_research": {"agent": "COMET", "model": "Perplexity", "priority": "medium"},
    "risk_assessment": {"agent": "MERLIN", "model": "Gemini", "priority": "high"},
    "strategy_planning": {"agent": "TRINITY", "model": "GPT", "priority": "medium"},
    "code_generation": {"agent": "ARKON-5", "model": "Claude", "priority": "low"},
    "infra_monitoring": {"agent": "WATCHDOG", "model": "internal", "priority": "low"},
    "dex_analysis": {"agent": "KIMI", "model": "Kimi", "priority": "medium"},
    "price_oracle": {"agent": "ORACLE", "model": "internal", "priority": "high"},
}


@app.route('/api/orchestrator/dispatch', methods=['POST'])
def api_orchestrator_dispatch():
    """Route a task to the best available agent."""
    body = request.get_json(silent=True) or {}
    task_type = body.get("task_type", "trading_analysis")
    intent = body.get("intent", "")
    priority = body.get("priority", "")
    auto_validate = body.get("auto_validate", False)

    route = ORCHESTRATOR_ROUTES.get(task_type, ORCHESTRATOR_ROUTES["trading_analysis"])
    agent = route["agent"]
    model = route["model"]
    if not priority:
        priority = route["priority"]

    ts = _utcnow_iso()
    state = _load_agents_state()
    _ensure_missions(state)

    # Check if target agent is online
    agent_info = state.get("agents", {}).get(agent, {})
    agent_online = agent_info.get("status") == "online"

    # Create mission
    mission_id = str(uuid.uuid4())[:8]
    mission = {
        "id": mission_id,
        "task_type": task_type,
        "intent": intent,
        "agent": agent,
        "model": model,
        "priority": priority,
        "status": "dispatched" if agent_online else "queued",
        "auto_validate": auto_validate,
        "created_at": ts,
    }

    state["missions"]["active"].append(mission)

    # Create control proposal
    proposals = state.get("control_queue", [])
    proposal = {
        "action_id": mission_id,
        "action_type": task_type,
        "source": "ORCHESTRATOR",
        "reason": intent,
        "agent": agent,
        "status": "validated" if auto_validate else "proposed",
        "ts": ts,
    }
    proposals.append(proposal)
    state["control_queue"] = proposals[-30:]

    _record_comet_intel(state,
        summary=f"DISPATCH: {task_type} -> {agent} ({model}) | {intent[:80]}",
        level="INFO", source="ORCHESTRATOR")

    _save_agents_state(state)

    # Broadcast SSE events
    _broadcast("control_update", {"queue": state.get("control_queue", [])})

    return jsonify({
        "ok": True,
        "mission_id": mission_id,
        "agent": agent,
        "model": model,
        "status": mission["status"],
        "agent_online": agent_online,
    })


@app.route('/api/orchestrator/build_loop', methods=['POST'])
def api_orchestrator_build_loop():
    """Start an autonomous build loop — decompose goal into agent tasks."""
    body = request.get_json(silent=True) or {}
    goal = body.get("goal", "")
    if not goal:
        return jsonify({"ok": False, "error": "goal required"}), 400

    ts = _utcnow_iso()
    state = _load_agents_state()
    _ensure_missions(state)

    # Decompose into standard sub-tasks
    subtasks = [
        {"type": "market_research", "intent": f"Research context for: {goal}"},
        {"type": "risk_assessment", "intent": f"Assess risks of: {goal}"},
        {"type": "strategy_planning", "intent": f"Plan strategy for: {goal}"},
        {"type": "trading_analysis", "intent": f"Analyze and decide: {goal}"},
    ]

    loop_id = str(uuid.uuid4())[:8]
    missions = []
    for i, task in enumerate(subtasks):
        route = ORCHESTRATOR_ROUTES.get(task["type"], {})
        mission = {
            "id": f"{loop_id}-{i}",
            "loop_id": loop_id,
            "step": i + 1,
            "total_steps": len(subtasks),
            "task_type": task["type"],
            "intent": task["intent"],
            "agent": route.get("agent", "MERLIN"),
            "model": route.get("model", "Gemini"),
            "status": "queued" if i > 0 else "dispatched",
            "created_at": ts,
        }
        missions.append(mission)
        state["missions"]["active"].append(mission)

    _record_comet_intel(state,
        summary=f"BUILD LOOP: {goal[:80]} | {len(subtasks)} steps | loop={loop_id}",
        level="INFO", source="ORCHESTRATOR")

    _save_agents_state(state)
    _broadcast("control_update", {"queue": state.get("control_queue", [])})

    return jsonify({
        "ok": True,
        "loop_id": loop_id,
        "goal": goal,
        "steps": len(subtasks),
        "missions": missions,
    })


# ── Auto-Configuration ─────────────────────────────────────

AUTOCONFIG_WHITELIST = {
    "pipeline.mode": ["dry_run", "authorized"],
    "pipeline.threat_level": ["T0", "T1", "T2", "T3"],
    "pipeline.kill_switch": [True, False],
    "agent.activate": None,
    "agent.deactivate": None,
}


@app.route('/api/autoconfig/apply', methods=['POST'])
def api_autoconfig_apply():
    """Apply a configuration change proposed by an agent."""
    if not _trinity_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    changes = body.get("changes", [])
    source = body.get("source", "AGENT")
    reason = body.get("reason", "auto-configuration")
    results = []

    state = _load_agents_state()
    pipeline = state.get("pipeline", {})

    for change in changes:
        key = change.get("key", "")
        value = change.get("value")

        if key not in AUTOCONFIG_WHITELIST:
            results.append({"key": key, "status": "rejected", "reason": "not whitelisted"})
            continue

        allowed = AUTOCONFIG_WHITELIST[key]
        if allowed is not None and value not in allowed:
            results.append({"key": key, "status": "rejected", "reason": f"value not allowed: {value}"})
            continue

        # Apply
        if key == "pipeline.mode":
            pipeline["mode"] = value
        elif key == "pipeline.threat_level":
            pipeline["threat_level"] = value
        elif key == "pipeline.kill_switch":
            pipeline["kill_switch"] = value
        elif key == "agent.activate" and isinstance(value, str):
            if value in state.get("agents", {}):
                state["agents"][value]["status"] = "online"
        elif key == "agent.deactivate" and isinstance(value, str):
            if value in state.get("agents", {}):
                state["agents"][value]["status"] = "standby"

        results.append({"key": key, "value": value, "status": "applied"})

    state["pipeline"] = pipeline
    _record_comet_intel(state,
        summary=f"AUTOCONFIG by {source}: {len(results)} changes | {reason[:80]}",
        level="INFO", source="AUTOCONFIG")
    _save_agents_state(state)

    _broadcast("mesh_update", {"mesh": {
        "agents": {k: {"status": v.get("status"), "last_seen": v.get("last_seen")}
                   for k, v in state.get("agents", {}).items()},
        "online": sum(1 for a in state.get("agents", {}).values() if a.get("status") == "online"),
        "total_agents": len(state.get("agents", {})),
        "missions_active": len(state["missions"]["active"]),
    }})

    return jsonify({"ok": True, "results": results, "source": source})



# -- HA Bridge Diagnostic Endpoints ----------------------------------------

@app.route('/api/ha/test', methods=['GET'])
def api_ha_test():
    """Live HA connectivity diagnostic."""
    ping = ha_bridge.ping()
    wallets = ha_bridge.get_wallet_status() if ping.get("ok") else {}
    pipeline = ha_bridge.get_state("sensor.s25_pipeline_status")
    return jsonify({
        "ok": ping.get("ok", False),
        "ha_url": ha_bridge.url,
        "ha_connected": ha_bridge.connected,
        "ping": ping,
        "pipeline": pipeline.get("state") if pipeline else None,
        "wallets_found": len(wallets),
    })


@app.route('/api/wallets', methods=['GET'])
def api_wallets():
    """Aggregated wallet status from HA sensors."""
    wallets = ha_bridge.get_wallet_status()
    return jsonify({"ok": True, "wallets": wallets})


# -- OpenAI-Compatible API for HA Conversation Agent -------------------------

AGENT_API_KEYS = {"s25-local-agent-key", "s25-jarvis-internal-key"}


def _agent_auth() -> bool:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:] in AGENT_API_KEYS or (S25_SECRET and auth[7:] == S25_SECRET)
    return False


@app.route('/v1/chat/completions', methods=['POST'])
def v1_chat_completions():
    """OpenAI-compatible chat completions — HA conversation agent endpoint."""
    if not _agent_auth():
        return jsonify({"error": {"message": "Invalid API key", "type": "auth_error"}}), 401
    body = request.get_json(silent=True) or {}
    result = handle_chat_completion(body, ha_bridge=ha_bridge, load_state_fn=_load_agents_state)
    return jsonify(result)


@app.route('/v1/models', methods=['GET'])
def v1_models():
    """OpenAI-compatible models list."""
    return jsonify(list_agent_models())


@app.route('/v1/models/<model_id>', methods=['GET'])
def v1_model_detail(model_id):
    """OpenAI-compatible model detail."""
    return jsonify({"id": model_id, "object": "model", "created": 1700000000, "owned_by": "s25-local"})


@app.route('/api/ha/agent', methods=['POST'])
def api_ha_agent():
    """Process a prompt via local AI and push response to HA sensors.
    Called by HA automation when input_text.s25_agent_prompt changes.
    Also callable as a webhook from HA."""
    body = request.get_json(silent=True) or {}
    prompt = body.get("prompt", body.get("text", ""))

    if not prompt:
        # Try to read from HA sensor directly
        if ha_bridge.connected:
            state = ha_bridge.get_state("input_text.s25_agent_prompt")
            if state:
                prompt = state.get("state", "")

    if not prompt or len(prompt) < 3:
        return jsonify({"ok": False, "error": "No prompt provided"}), 400

    # Update HA: processing
    ha_bridge.push_sensor("sensor.s25_local_agent_status", "processing", {
        "friendly_name": "S25 Agent Local Status",
        "prompt": prompt[:100],
        "icon": "mdi:brain",
    })

    # Call local conversation agent
    result = handle_chat_completion(
        {"model": "s25-lumiere", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
        ha_bridge=ha_bridge,
        load_state_fn=_load_agents_state,
    )

    reply = result.get("choices", [{}])[0].get("message", {}).get("content", "Erreur")

    # Push response to HA
    ha_bridge.push_sensor("input_text.s25_agent_response", reply[:255], {
        "friendly_name": "S25 Agent Response",
        "full_response": reply,
        "model": "s25-lumiere",
        "icon": "mdi:robot",
    })
    ha_bridge.push_sensor("sensor.s25_local_agent_status", "ready", {
        "friendly_name": "S25 Agent Local Status",
        "last_prompt": prompt[:100],
        "last_reply_length": len(reply),
        "icon": "mdi:brain",
    })

    return jsonify({"ok": True, "reply": reply, "model": "s25-lumiere"})


@app.route('/webhook/s25_agent', methods=['POST'])
def webhook_s25_agent():
    """Webhook endpoint for HA to call the local agent."""
    return api_ha_agent()


@app.route('/api/mesh/heartbeat', methods=['POST', 'GET'])
def api_mesh_heartbeat():
    """Push full mesh + market data to HA sensors. Called by cron or manually."""
    result = push_mesh_to_ha(ha_bridge, _load_agents_state)
    return jsonify(result)


@app.route('/api/market/live', methods=['GET'])
def api_market_live():
    """Aggregated live market data — prices, fear&greed, trending, global."""
    from agents.ninja_routes import (
        get_prices, get_fear_greed, get_trending,
        get_global_market,
    )
    result = {"timestamp": datetime.utcnow().isoformat(), "source": "ninja_free"}

    try:
        coins = ["bitcoin", "ethereum", "dogecoin", "solana", "cosmos", "akash-network",
                 "chainlink", "uniswap", "aave", "maker"]
        prices = get_prices(coins)
        result["prices"] = {}
        for coin, data in (prices or {}).items():
            result["prices"][coin] = {
                "usd": data.get("usd", 0),
                "change_24h": round(data.get("usd_24h_change", 0), 2),
            }
    except Exception as e:
        result["prices_error"] = str(e)

    try:
        fg = get_fear_greed(7)
        if fg:
            result["fear_greed"] = {
                "current": {"value": int(fg[0]["value"]), "label": fg[0]["label"]},
                "history_7d": [{"value": int(d["value"]), "label": d["label"]} for d in fg],
            }
    except Exception as e:
        result["fear_greed_error"] = str(e)

    try:
        trending = get_trending()
        if trending:
            result["trending"] = [
                {"name": t["name"], "symbol": t["symbol"], "rank": t.get("market_cap_rank")}
                for t in trending[:10]
            ]
    except Exception as e:
        result["trending_error"] = str(e)

    try:
        gm = get_global_market()
        if gm:
            result["global"] = {
                "total_market_cap_usd": round(gm.get("total_market_cap_usd", 0)),
                "total_volume_24h_usd": round(gm.get("total_volume_24h_usd", 0)),
                "btc_dominance": round(gm.get("btc_dominance", 0), 2),
                "eth_dominance": round(gm.get("eth_dominance", 0), 2),
                "active_cryptocurrencies": gm.get("active_cryptocurrencies", 0),
            }
    except Exception as e:
        result["global_error"] = str(e)

    return jsonify(result)


@app.route('/api/system/health', methods=['GET'])
def api_system_health():
    """Full system health — all services, agents, connectivity."""
    import subprocess
    health = {
        "timestamp": datetime.utcnow().isoformat(),
        "cockpit": {"status": "online", "pid": os.getpid(), "uptime_s": int(time.time() - _START_TIME)},
    }

    # HA connectivity
    try:
        r = ha_bridge.ping()
        health["ha"] = {"connected": r.get("ok", False), "url": "10.0.0.136:8123"}
    except Exception:
        health["ha"] = {"connected": False}

    # Ollama
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        health["ollama"] = {"status": "online", "models": models}
    except Exception:
        health["ollama"] = {"status": "offline"}

    # Docker containers
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}:{{.Status}}"],
            timeout=5, text=True
        )
        health["docker"] = {
            line.split(":")[0]: line.split(":", 1)[1]
            for line in out.strip().split("\n") if ":" in line
        }
    except Exception:
        health["docker"] = {"error": "cannot check"}

    # Agents
    state = _load_agents_state()
    agents = state.get("agents", {})
    online = [k for k, v in agents.items() if v.get("status") == "online"]
    health["agents"] = {"online": len(online), "total": len(agents), "list": online}

    # Cloudflare tunnels
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", "cloudflared"],
            timeout=3, text=True
        )
        health["cloudflare"] = {"tunnels": "running", "pids": out.strip().split("\n")}
    except Exception:
        health["cloudflare"] = {"tunnels": "not running"}

    # Disk
    try:
        out = subprocess.check_output(["df", "-h", "/"], timeout=3, text=True)
        line = out.strip().split("\n")[-1].split()
        health["disk"] = {"total": line[1], "used": line[2], "avail": line[3], "pct": line[4]}
    except Exception:
        pass

    # GPU
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            timeout=5, text=True
        )
        parts = out.strip().split(", ")
        health["gpu"] = {
            "temp_c": int(parts[0]),
            "vram_used_mb": int(parts[1]),
            "vram_total_mb": int(parts[2]),
            "utilization_pct": int(parts[3]),
        }
    except Exception:
        health["gpu"] = {"status": "no nvidia-smi"}

    return jsonify(health)




# ════ ALERTS ENGINE INJECTION ════
# Intelligent rule-based alerts — evaluates market + infra metrics,
# dispatches to intel feed, HA notifications, and trading signals.

def _alerts_collect_metrics() -> dict:
    """Build metrics snapshot via threaded self-HTTP calls."""
    base = "http://localhost:" + str(os.environ.get("PORT", "7777"))
    try:
        market = requests.get(base + "/api/market/live", timeout=15).json()
    except Exception:
        market = {}
    try:
        health = requests.get(base + "/api/system/health", timeout=15).json()
    except Exception:
        health = {}

    metrics = {}
    # Market
    metrics["prices"] = market.get("prices", {})
    if market.get("fear_greed"):
        metrics["fear_greed"] = market["fear_greed"]
    metrics["global"] = market.get("global", {})
    # Health
    for key in ("ha", "ollama", "docker", "agents", "cloudflare", "disk", "gpu", "cockpit"):
        if key in health:
            metrics[key] = health[key]
    return metrics


def _alerts_get_nested(d, path, default=None):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


def _alerts_dispatch(rule: dict, metrics: dict) -> dict:
    """Execute a firing rule's actions and return a per-action result map."""
    result = {"rule": rule["id"], "dispatched": [], "errors": []}
    actions = rule.get("actions", [])
    sev = rule.get("severity", "info").upper()
    body_msg = f"[{sev}] {rule['name']}: {rule['description']}"

    # intel → comet feed
    if "intel" in actions:
        try:
            state = _load_agents_state()
            _ensure_intel(state)
            _record_comet_intel(state, summary=body_msg, level=sev, source="ALERTS")
            _save_agents_state(state)
            result["dispatched"].append("intel")
        except Exception as e:
            result["errors"].append(f"intel: {e}")

    # ha_notify → mobile push
    if "ha_notify" in actions:
        try:
            ok = ha_bridge.notify(
                message=rule["description"],
                title=f"S25 Alert — {rule['name']}",
                tag=f"s25_alert_{rule['id']}",
                importance="high" if sev == "CRITICAL" else "default",
            )
            result["dispatched"].append(f"ha_notify:{bool(ok)}")
        except Exception as e:
            result["errors"].append(f"ha_notify: {e}")

    # signal → /api/signal via test_client (weighted, consensus-aware)
    if "signal" in actions and rule.get("signal_payload"):
        try:
            payload = dict(rule["signal_payload"])
            btc_price = _alerts_get_nested(metrics, "prices.bitcoin.usd", 0) or 0
            eth_price = _alerts_get_nested(metrics, "prices.ethereum.usd", 0) or 0
            doge_price = _alerts_get_nested(metrics, "prices.dogecoin.usd", 0) or 0
            sym = payload.get("symbol", "")
            if sym.startswith("BTC"):
                payload["price"] = float(btc_price)
            elif sym.startswith("ETH"):
                payload["price"] = float(eth_price)
            elif sym.startswith("DOGE"):
                payload["price"] = float(doge_price)
            base = "http://localhost:" + str(os.environ.get("PORT", "7777"))
            resp = requests.post(base + "/api/signal", json=payload, timeout=10)
            result["dispatched"].append(f"signal:{resp.status_code}")
        except Exception as e:
            result["errors"].append(f"signal: {e}")

    return result


@app.route('/api/alerts/rules', methods=['GET'])
def api_alerts_rules():
    try:
        from agents.alert_rules import list_rules as _ls
    except Exception as e:
        return jsonify({"ok": False, "error": f"alert_rules import failed: {e}"}), 500
    rules = _ls()
    return jsonify({"ok": True, "rules": rules, "count": len(rules)})


@app.route('/api/alerts/state', methods=['GET'])
def api_alerts_state():
    try:
        from agents.alert_rules import get_state as _gs
    except Exception as e:
        return jsonify({"ok": False, "error": f"alert_rules import failed: {e}"}), 500
    return jsonify({"ok": True, "state": _gs()})


@app.route('/api/alerts/evaluate', methods=['POST', 'GET'])
def api_alerts_evaluate():
    """Run the rule engine against live metrics and dispatch firing rules."""
    try:
        from agents.alert_rules import evaluate_all as _eval
    except Exception as e:
        return jsonify({"ok": False, "error": f"alert_rules import failed: {e}"}), 500

    metrics = _alerts_collect_metrics()
    result = _eval(metrics)

    dispatched = []
    for rule in result.get("firing", []):
        dispatched.append(_alerts_dispatch(rule, metrics))
    result["dispatched"] = dispatched
    if request.args.get("debug"):
        result["_metrics_snapshot"] = metrics
    result["ok"] = True
    return jsonify(result)

# ════ END ALERTS ENGINE INJECTION ════




# ════ TERMINAL UI INJECTION ════
# MetaTrader-style terminal served on /terminal.
# Frontend is a single self-contained HTML (static/terminal.html) that embeds
# TradingView Advanced Chart widget and polls /api/terminal/summary every 10s.

from flask import send_from_directory as _send_from_directory

_TERMINAL_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.route('/terminal', methods=['GET'])
def terminal_ui():
    """Serve the MetaTrader-style terminal single-page app."""
    try:
        return _send_from_directory(_TERMINAL_STATIC_DIR, "terminal.html")
    except Exception as e:
        return jsonify({"ok": False, "error": f"terminal.html not found: {e}"}), 404


def _terminal_local_base() -> str:
    port = os.environ.get("PORT", "7777")
    return f"http://127.0.0.1:{port}"


@app.route('/api/terminal/summary', methods=['GET'])
def api_terminal_summary():
    """Aggregated payload for the terminal dashboard.

    Single call returns everything the UI needs:
        - market (prices + fear_greed + global)
        - mesh (online/total/agents)
        - pipeline (mode/verdict/threat/kill_switch/last_signal/buffer)
        - intel (last N comet_feed entries, newest first)
        - wallet (from /api/wallet/status)
        - dex (from agents_state.dex or empty)
    """
    base = _terminal_local_base()

    market = {}
    try:
        r = requests.get(base + "/api/market/live", timeout=10)
        if r.ok:
            market = r.json() or {}
    except Exception as e:
        market = {"error": str(e)}

    wallet = {}
    try:
        r = requests.get(base + "/api/wallet/status", timeout=10)
        if r.ok:
            wallet = r.json() or {}
    except Exception as e:
        wallet = {"error": str(e)}

    try:
        state = _load_agents_state()
    except Exception:
        state = {}

    # Mesh
    agents = state.get("agents", {}) if isinstance(state, dict) else {}
    mesh_total = len(agents) if isinstance(agents, dict) else 0
    mesh_online = 0
    if isinstance(agents, dict):
        for _aid, _info in agents.items():
            if isinstance(_info, dict) and _info.get("status") in ("online", "running", "ok"):
                mesh_online += 1

    # Pipeline
    pipeline = state.get("pipeline", {}) if isinstance(state, dict) else {}
    last_signal = None
    try:
        sig_buf = state.get("signals", {}).get("buffer", []) if isinstance(state, dict) else []
        if sig_buf:
            last_signal = sig_buf[-1]
    except Exception:
        last_signal = None

    # Intel (newest first, last 30)
    try:
        feed = state.get("intel", {}).get("comet_feed", [])
        intel = list(reversed(feed))[:30]
    except Exception:
        intel = []

    # DEX
    dex = state.get("dex", {}) if isinstance(state, dict) else {}

    # Kill switch
    kill_switch = False
    try:
        kill_switch = bool(state.get("kill_switch", {}).get("enabled", False))
    except Exception:
        kill_switch = False

    # Mode / verdict / threat
    mode = pipeline.get("mode") if isinstance(pipeline, dict) else None
    verdict = pipeline.get("verdict") if isinstance(pipeline, dict) else None
    threat = pipeline.get("threat_level") if isinstance(pipeline, dict) else None
    if not mode:
        mode = state.get("mode") if isinstance(state, dict) else None

    return jsonify({
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "market": {
            "prices": market.get("prices", {}),
            "fear_greed": market.get("fear_greed", {}),
            "global": market.get("global", {}),
        },
        "mesh": {
            "online": mesh_online,
            "total": mesh_total,
            "agents": agents if isinstance(agents, dict) else {},
        },
        "pipeline": {
            "mode": mode,
            "verdict": verdict,
            "threat_level": threat,
            "kill_switch": kill_switch,
            "last_signal": last_signal,
            "buffer_size": len(state.get("signals", {}).get("buffer", [])) if isinstance(state, dict) else 0,
        },
        "intel": intel,
        "wallet": wallet,
        "dex": dex,
    })

# ════ END TERMINAL UI INJECTION ════


if __name__ == '__main__':
    port = int(os.getenv("PORT", "7777"))
    app.run(host='0.0.0.0', port=port, debug=False)
