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
from agents.ha_bridge import ha as ha_bridge

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

    # Push signal to Home Assistant (sensors + MEXC execution)
    ha_result = None
    try:
        ha_result = _ha_push_signal(action, symbol, confidence, effective_confidence, price, reason, verdict, source)
    except Exception as _ha_err:
        ha_result = {"ok": False, "error": str(_ha_err)}

    return jsonify({
        "ok": True, "mode": mode, "symbol": symbol, "action": action, "verdict": verdict,
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
    }
    weight = TV_WEIGHTS.get("TRADINGVIEW", 0.85)
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

    signals_buffer.append({"symbol": symbol, "action": normalized_action, "source": "TRADINGVIEW",
                          "confidence": confidence, "ts": ts, "strategy": strategy, "interval": interval})
    pipeline["signals_buffer"] = signals_buffer[-20:]
    pipeline["last_signal"] = {
        "symbol": symbol, "action": normalized_action, "confidence": confidence,
        "weight": weight, "weighted_confidence": weighted_confidence,
        "consensus": consensus, "consensus_bonus": consensus_bonus,
        "effective_confidence": effective_confidence,
        "price": price, "reason": reason, "source": "TRADINGVIEW",
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
        ha_result = _ha_push_signal(normalized_action, symbol, confidence, effective_confidence, price, reason, verdict, "TRADINGVIEW")
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
                                         reason=reason, source="TRADINGVIEW")
        except Exception as e:
            dex_result = {"error": str(e)}

    return jsonify({
        "ok": True, "source": "TRADINGVIEW", "symbol": symbol,
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
#  GET /api/trading/overview — Unified multi-chain trading dashboard
# ═══════════════════════════════════════════════════════════════

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

    return jsonify({"ok": True, "trading": overview})






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


if __name__ == '__main__':
    port = int(os.getenv("PORT", "7777"))
    app.run(host='0.0.0.0', port=port, debug=False)
