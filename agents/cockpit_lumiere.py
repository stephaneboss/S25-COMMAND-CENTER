"""
S25 Lumière — Cockpit Web UI
==============================
Interface de commandement temps réel pour le système S25.
Futuriste, dark mode, live updates via SSE.

Port: 7777 (configurable via PORT env var)
"""

import os
import json
import time
import threading
import subprocess
from datetime import datetime, timedelta
from flask import Flask, render_template_string, Response, jsonify
import requests

app = Flask(__name__)

# Register COMET bridge routes
try:
    from agents.comet_bridge import register_comet_routes
    _comet_routes_registered = True
except ImportError:
    try:
        from comet_bridge import register_comet_routes
        _comet_routes_registered = True
    except ImportError:
        _comet_routes_registered = False

# ─── Config ──────────────────────────────────────────────────────────
HA_URL      = os.getenv("HA_URL",      "http://homeassistant.local:8123")
HA_TOKEN    = os.getenv("HA_TOKEN",    "")
PORT        = int(os.getenv("PORT",    "7777"))
VERSION     = "2.0.0"
BUILD_DATE  = "2026-03"

# ─── HTML Template ───────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>S25 LUMIÈRE — Command Center</title>
<style>
  :root {
    --bg:        #05050f;
    --bg2:       #0a0a1a;
    --bg3:       #0f0f25;
    --border:    #1a1a3a;
    --green:     #00ff88;
    --blue:      #00aaff;
    --orange:    #ff8800;
    --red:       #ff2244;
    --yellow:    #ffdd00;
    --text:      #c8d0e8;
    --text-dim:  #556080;
    --font:      'Courier New', monospace;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* ── Header ── */
  header {
    background: linear-gradient(135deg, #05050f 0%, #0a0a2a 100%);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
  }
  .logo {
    display: flex; align-items: center; gap: 12px;
  }
  .logo-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--green), var(--blue));
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: bold; color: #000;
  }
  .logo-text { font-size: 20px; font-weight: bold; letter-spacing: 4px; color: var(--green); }
  .logo-sub  { font-size: 10px; color: var(--text-dim); letter-spacing: 2px; margin-top: 2px; }
  .header-right { display: flex; align-items: center; gap: 16px; }
  .clock { font-size: 14px; color: var(--blue); letter-spacing: 2px; }
  .version { font-size: 10px; color: var(--text-dim); }
  .status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%,100% { opacity:1; } 50% { opacity:0.4; }
  }

  /* ── Grid ── */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
    padding: 20px;
    max-width: 1600px;
    margin: 0 auto;
  }

  /* ── Cards ── */
  .card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: border-color .3s;
  }
  .card:hover { border-color: #2a2a5a; }
  .card::before {
    content: '';
    position: absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, var(--green), var(--blue));
  }
  .card-title {
    font-size: 10px; letter-spacing: 3px; color: var(--text-dim);
    text-transform: uppercase; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
  }
  .card-title span { color: var(--blue); }

  /* ── Threat Level ── */
  .threat-card { grid-column: span 2; }
  .threat-levels { display: flex; gap: 12px; margin-top: 8px; }
  .threat-level {
    flex: 1; padding: 16px 12px;
    border-radius: 8px; border: 2px solid transparent;
    text-align: center; cursor: default;
    transition: all .3s;
    position: relative; overflow: hidden;
  }
  .threat-level.active { border-color: currentColor; }
  .threat-level.active::after {
    content: '';
    position: absolute; inset: 0;
    background: currentColor; opacity: 0.08;
  }
  .t0 { color: var(--green);  }
  .t1 { color: var(--yellow); }
  .t2 { color: var(--orange); }
  .t3 { color: var(--red);    }
  .threat-num  { font-size: 28px; font-weight: bold; }
  .threat-name { font-size: 10px; letter-spacing: 2px; margin-top: 4px; }

  /* ── Signal ── */
  .signal-big {
    font-size: 48px; font-weight: bold; letter-spacing: 4px;
    text-align: center; padding: 20px 0;
    text-shadow: 0 0 30px currentColor;
  }
  .sig-buy  { color: var(--green);  }
  .sig-sell { color: var(--red);    }
  .sig-hold { color: var(--yellow); }
  .sig-none { color: var(--text-dim); font-size: 24px; }

  .confidence-bar {
    height: 6px; background: var(--border);
    border-radius: 3px; margin: 8px 0;
    overflow: hidden;
  }
  .confidence-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--blue), var(--green));
    border-radius: 3px;
    transition: width 1s;
  }

  /* ── Agents ── */
  .agent-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
  }
  .agent-row:last-child { border-bottom: none; }
  .agent-dot {
    width: 8px; height: 8px; border-radius: 50%;
    flex-shrink: 0;
  }
  .dot-green  { background: var(--green);  box-shadow: 0 0 6px var(--green);  }
  .dot-orange { background: var(--orange); box-shadow: 0 0 6px var(--orange); }
  .dot-red    { background: var(--red);    box-shadow: 0 0 6px var(--red);    }
  .dot-grey   { background: var(--text-dim); }
  .agent-name { flex: 1; font-size: 13px; }
  .agent-status { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; }

  /* ── Metrics ── */
  .metric-row {
    display: flex; justify-content: space-between;
    align-items: center; padding: 8px 0;
    border-bottom: 1px solid var(--border);
  }
  .metric-row:last-child { border-bottom: none; }
  .metric-label { font-size: 12px; color: var(--text-dim); }
  .metric-value { font-size: 14px; font-weight: bold; }
  .val-green  { color: var(--green);  }
  .val-orange { color: var(--orange); }
  .val-red    { color: var(--red);    }
  .val-blue   { color: var(--blue);   }

  /* ── Log feed ── */
  .log-feed {
    max-height: 200px; overflow-y: auto;
    font-size: 11px; line-height: 1.8;
    color: var(--text-dim);
  }
  .log-feed::-webkit-scrollbar { width: 4px; }
  .log-feed::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
  .log-entry { padding: 2px 0; border-bottom: 1px solid #0f0f25; }
  .log-ts   { color: #333; }
  .log-ok   { color: var(--green);  }
  .log-warn { color: var(--orange); }
  .log-err  { color: var(--red);    }
  .log-info { color: var(--blue);   }

  /* ── Big numbers ── */
  .big-num { font-size: 36px; font-weight: bold; color: var(--green); }
  .big-unit { font-size: 14px; color: var(--text-dim); margin-left: 4px; }

  /* ── Buttons ── */
  .btn-row { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; }
  .btn {
    padding: 8px 16px; border-radius: 6px;
    border: 1px solid; font-family: var(--font);
    font-size: 11px; letter-spacing: 1px;
    cursor: pointer; text-transform: uppercase;
    transition: all .2s; background: transparent;
  }
  .btn-green { border-color: var(--green); color: var(--green); }
  .btn-green:hover { background: rgba(0,255,136,0.1); }
  .btn-red   { border-color: var(--red);   color: var(--red);   }
  .btn-red:hover { background: rgba(255,34,68,0.1); }
  .btn-blue  { border-color: var(--blue);  color: var(--blue);  }
  .btn-blue:hover { background: rgba(0,170,255,0.1); }

  /* ── Footer ── */
  footer {
    text-align: center; padding: 20px;
    color: var(--text-dim); font-size: 10px;
    letter-spacing: 2px; border-top: 1px solid var(--border);
    margin-top: 20px;
  }

  /* ── Responsive ── */
  @media (max-width: 768px) {
    .threat-card { grid-column: span 1; }
    .threat-levels { flex-wrap: wrap; }
    .logo-text { font-size: 14px; }
    .signal-big { font-size: 36px; }
  }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">S²⁵</div>
    <div>
      <div class="logo-text">LUMIÈRE</div>
      <div class="logo-sub">S25 COMMAND CENTER v{{ version }}</div>
    </div>
  </div>
  <div class="header-right">
    <div class="status-dot" id="conn-dot" title="Live connection"></div>
    <div>
      <div class="clock" id="clock">--:--:--</div>
      <div class="version">{{ build_date }} — AKASH CLOUD</div>
    </div>
  </div>
</header>

<div class="grid">

  <!-- ── Threat Level ── -->
  <div class="card threat-card">
    <div class="card-title">🛡️ <span>NIVEAU DE MENACE</span> — PROTOCOLE T0/T3</div>
    <div class="threat-levels">
      <div class="threat-level t0" id="t0">
        <div class="threat-num">T0</div>
        <div class="threat-name">🟢 NORMAL</div>
      </div>
      <div class="threat-level t1" id="t1">
        <div class="threat-num">T1</div>
        <div class="threat-name">🟡 SURVEILLANCE</div>
      </div>
      <div class="threat-level t2" id="t2">
        <div class="threat-num">T2</div>
        <div class="threat-name">🟠 ALERTE</div>
      </div>
      <div class="threat-level t3" id="t3">
        <div class="threat-num">T3</div>
        <div class="threat-name">🔴 CRITIQUE</div>
      </div>
    </div>
  </div>

  <!-- ── ARKON Signal ── -->
  <div class="card">
    <div class="card-title">📡 <span>ARKON-5</span> — SIGNAL TRADING</div>
    <div class="signal-big sig-none" id="signal-action">STANDBY</div>
    <div style="display:flex;justify-content:space-between;margin-bottom:4px">
      <span id="signal-symbol" style="color:var(--blue);font-size:13px">---</span>
      <span id="signal-price" style="font-size:13px">$ ---</span>
    </div>
    <div class="confidence-bar">
      <div class="confidence-fill" id="conf-bar" style="width:0%"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-dim)">
      <span>Confidence: <span id="signal-conf" style="color:var(--green)">--</span></span>
      <span id="signal-ts">--:--</span>
    </div>
  </div>

  <!-- ── Risk ── -->
  <div class="card">
    <div class="card-title">⚡ <span>RISK GUARDIAN</span> — CIRCUIT BREAKER</div>
    <div class="metric-row">
      <span class="metric-label">Trading Status</span>
      <span class="metric-value val-green" id="trading-status">ACTIVE</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Circuit Breaker</span>
      <span class="metric-value val-green" id="circuit-breaker">CLOSED</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Daily P&amp;L</span>
      <span class="metric-value val-blue" id="daily-pnl">$ 0.00</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Open Positions</span>
      <span class="metric-value" id="open-positions">0 / 5</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Max Daily Loss</span>
      <span class="metric-value val-orange">5.0%</span>
    </div>
  </div>

  <!-- ── MEXC ── -->
  <div class="card">
    <div class="card-title">💱 <span>MEXC EXECUTOR</span> — ORDRE RÉCENT</div>
    <div class="metric-row">
      <span class="metric-label">Mode</span>
      <span class="metric-value val-orange" id="mexc-mode">DRY RUN</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Dernier Ordre</span>
      <span class="metric-value val-blue" id="mexc-last">---</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Status</span>
      <span class="metric-value" id="mexc-status">---</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Total Exécutés</span>
      <span class="metric-value" id="mexc-total">0</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">API Keys</span>
      <span class="metric-value val-orange" id="mexc-keys">NOT SET</span>
    </div>
  </div>

  <!-- ── Agents Network ── -->
  <div class="card">
    <div class="card-title">🤖 <span>AGENTS NETWORK</span> — STATUS</div>
    <div id="agents-list">
      <div class="agent-row">
        <div class="agent-dot dot-green"></div>
        <div class="agent-name">MERLIN (Gemini)</div>
        <div class="agent-status">ONLINE</div>
      </div>
      <div class="agent-row">
        <div class="agent-dot dot-green"></div>
        <div class="agent-name">COMET (Perplexity)</div>
        <div class="agent-status">ACTIVE</div>
      </div>
      <div class="agent-row">
        <div class="agent-dot dot-green"></div>
        <div class="agent-name">ARKON-5 (Gemini)</div>
        <div class="agent-status">READY</div>
      </div>
      <div class="agent-row">
        <div class="agent-dot dot-orange"></div>
        <div class="agent-name">MEXC EXECUTOR</div>
        <div class="agent-status">DRY RUN</div>
      </div>
      <div class="agent-row">
        <div class="agent-dot dot-green"></div>
        <div class="agent-name">RISK GUARDIAN</div>
        <div class="agent-status">IDLE</div>
      </div>
      <div class="agent-row">
        <div class="agent-dot dot-grey"></div>
        <div class="agent-name">TREASURY ENGINE</div>
        <div class="agent-status">PENDING</div>
      </div>
    </div>
  </div>

  <!-- ── System Health ── -->
  <div class="card">
    <div class="card-title">❤️ <span>SYSTEM HEALTH</span> — AKASH + HA</div>
    <div class="metric-row">
      <span class="metric-label">HA Connection</span>
      <span class="metric-value" id="ha-status">CHECKING...</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Akash DSEQ</span>
      <span class="metric-value val-blue">25822281</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Uptime</span>
      <span class="metric-value val-green" id="uptime">---</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">CPU Usage</span>
      <span class="metric-value" id="cpu-usage">---</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Memory</span>
      <span class="metric-value" id="mem-usage">---</span>
    </div>
  </div>

  <!-- ── AKT Balance ── -->
  <div class="card">
    <div class="card-title">💰 <span>TREASURY</span> — AKT + PORTFOLIO</div>
    <div style="padding:12px 0 8px">
      <span class="big-num" id="akt-balance">~20</span>
      <span class="big-unit">AKT</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Valeur AKT</span>
      <span class="metric-value val-green" id="akt-usd">$ --</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Akash Escrow</span>
      <span class="metric-value val-blue">~5 mois</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">GPU Node (DSEQ 25708774)</span>
      <span class="metric-value val-orange">~1 jour</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Auto-Treasury (ATOM→AKT)</span>
      <span class="metric-value val-orange">DISABLED</span>
    </div>
  </div>

  <!-- ── COMET Intel Feed ── -->
  <div class="card">
    <div class="card-title">🌐 <span>COMET</span> — PERPLEXITY WATCHMAN INTEL</div>
    <div class="log-feed" id="comet-feed">
      <div class="log-entry"><span class="log-ts">[INIT]</span> <span class="log-info">En attente du signal COMET...</span></div>
    </div>
    <div style="margin-top:8px;font-size:10px;color:var(--text-dim)">
      Bridge: <span style="color:var(--blue)" id="comet-ping">CHECKING...</span>
      &nbsp;|&nbsp; Endpoint: <span style="color:var(--text-dim)">/api/intel</span>
    </div>
  </div>

  <!-- ── Live Log ── -->
  <div class="card" style="grid-column: span 2">
    <div class="card-title">📋 <span>LIVE FEED</span> — EVENTS S25</div>
    <div class="log-feed" id="log-feed">
      <div class="log-entry"><span class="log-ts">[BOOT]</span> <span class="log-ok">S25 Lumière Cockpit v{{ version }} démarré</span></div>
      <div class="log-entry"><span class="log-ts">[BOOT]</span> <span class="log-info">Connexion HA en cours...</span></div>
    </div>
    <div class="btn-row">
      <button class="btn btn-green" onclick="addLog('MANUAL', 'info', 'Rafraîchissement manuel')">↻ Refresh</button>
      <button class="btn btn-red"   onclick="triggerKillSwitch()">🚨 KILL SWITCH</button>
      <button class="btn btn-blue"  onclick="window.open('{{ ha_url }}','_blank')">🏠 Open HA</button>
    </div>
  </div>

</div>

<footer>
  S25 LUMIÈRE COMMAND CENTER — AKASH CLOUD — BUILT BY CLAUDE FOR MAJOR STEF — {{ build_date }}
</footer>

<script>
const HA_URL = "{{ ha_url }}";

// ── Clock ──────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  const t = now.toISOString().replace('T',' ').substring(0,19) + ' UTC';
  document.getElementById('clock').textContent = t;
}
setInterval(updateClock, 1000);
updateClock();

// ── Uptime ────────────────────────────────────────────────────────
const startTime = Date.now();
setInterval(() => {
  const s = Math.floor((Date.now() - startTime) / 1000);
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60;
  document.getElementById('uptime').textContent =
    `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
}, 1000);

// ── Log feed ──────────────────────────────────────────────────────
function addLog(ts, level, msg) {
  const feed = document.getElementById('log-feed');
  const div  = document.createElement('div');
  div.className = 'log-entry';
  const now = new Date().toTimeString().substring(0,8);
  div.innerHTML = `<span class="log-ts">[${ts||now}]</span> <span class="log-${level}">${msg}</span>`;
  feed.insertBefore(div, feed.firstChild);
  while (feed.children.length > 50) feed.removeChild(feed.lastChild);
}

// ── Set threat level ──────────────────────────────────────────────
function setThreat(level) {
  ['t0','t1','t2','t3'].forEach(t => document.getElementById(t).classList.remove('active'));
  const el = document.getElementById('t'+level);
  if (el) el.classList.add('active');
}
setThreat(0);

// ── Set signal ────────────────────────────────────────────────────
function setSignal(action, symbol, confidence, price) {
  const el = document.getElementById('signal-action');
  el.className = 'signal-big';
  if      (action === 'BUY')  { el.classList.add('sig-buy');  el.textContent = '▲ BUY'; }
  else if (action === 'SELL') { el.classList.add('sig-sell'); el.textContent = '▼ SELL'; }
  else if (action === 'HOLD') { el.classList.add('sig-hold'); el.textContent = '◆ HOLD'; }
  else                        { el.classList.add('sig-none'); el.textContent = 'STANDBY'; }

  if (symbol)     document.getElementById('signal-symbol').textContent = symbol;
  if (price)      document.getElementById('signal-price').textContent  = '$ '+price.toLocaleString();
  if (confidence !== undefined) {
    document.getElementById('signal-conf').textContent = (confidence*100).toFixed(0)+'%';
    document.getElementById('conf-bar').style.width = (confidence*100)+'%';
  }
  document.getElementById('signal-ts').textContent = new Date().toTimeString().substring(0,8);
}

// ── Fetch status from cockpit API ─────────────────────────────────
async function fetchStatus() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();

    // Threat
    setThreat(d.threat_level || 0);

    // Signal
    if (d.signal) {
      setSignal(d.signal.action, d.signal.symbol, d.signal.confidence, d.signal.price);
      if (d.signal.action && d.signal.action !== 'HOLD') {
        addLog(null, d.signal.action==='BUY'?'ok':'err',
          `${d.signal.action} ${d.signal.symbol} @ ${d.signal.price} conf=${Math.round((d.signal.confidence||0)*100)}%`);
      }
    }

    // HA status
    const haEl = document.getElementById('ha-status');
    if (d.ha_online) {
      haEl.textContent = 'CONNECTED';
      haEl.className   = 'metric-value val-green';
    } else {
      haEl.textContent = 'OFFLINE';
      haEl.className   = 'metric-value val-red';
    }

    // CPU/Mem
    if (d.cpu !== undefined)
      document.getElementById('cpu-usage').textContent = d.cpu.toFixed(1) + '%';
    if (d.memory !== undefined)
      document.getElementById('mem-usage').textContent = d.memory.toFixed(1) + '%';

    // AKT price
    if (d.akt_price)
      document.getElementById('akt-usd').textContent = '$ '+d.akt_price.toFixed(3);

    document.getElementById('conn-dot').style.background = 'var(--green)';
  } catch(e) {
    document.getElementById('conn-dot').style.background = 'var(--red)';
    addLog(null, 'err', 'API status error: '+e.message);
  }
}

// ── Kill switch ───────────────────────────────────────────────────
async function triggerKillSwitch() {
  if (!confirm('⚠️ ACTIVER LE KILL SWITCH S25 ?\nCela va arrêter tous les agents.')) return;
  addLog(null, 'err', '🚨 KILL SWITCH activé par opérateur');
  try {
    await fetch('/api/kill-switch', { method: 'POST' });
  } catch(e) {}
}

// ── COMET intel feed ──────────────────────────────────────────────
async function fetchCometFeed() {
  try {
    const r = await fetch('/api/comet/feed?n=10');
    const d = await r.json();
    if (!d.ok || !d.feed.length) return;

    const feed = document.getElementById('comet-feed');
    feed.innerHTML = '';
    d.feed.forEach(entry => {
      const div = document.createElement('div');
      div.className = 'log-entry';
      const lvl = entry.level === 'CRITICAL' ? 'err'
                : entry.level === 'ALERT'    ? 'warn'
                : entry.level === 'WARNING'  ? 'warn'
                : 'info';
      const ts = (entry.ts||'').substring(11,19);
      div.innerHTML = `<span class="log-ts">[${ts}]</span> <span class="log-${lvl}">[${entry.source}] ${entry.summary}</span>`;
      feed.appendChild(div);
    });

    document.getElementById('comet-ping').textContent = 'CONNECTED';
    document.getElementById('comet-ping').style.color = 'var(--green)';
  } catch(e) {
    document.getElementById('comet-ping').textContent = 'OFFLINE';
    document.getElementById('comet-ping').style.color = 'var(--red)';
  }
}
setInterval(fetchCometFeed, 15000);
fetchCometFeed();

// ── Poll ──────────────────────────────────────────────────────────
setInterval(fetchStatus, 10000);
fetchStatus();
addLog('INIT', 'ok', 'Cockpit connecté — polling toutes les 10s');
</script>
</body>
</html>
"""

# ─── State (in-memory, simple) ───────────────────────────────────────
state = {
    "threat_level": 0,
    "signal": {
        "action": None,
        "symbol": None,
        "confidence": 0,
        "price": 0,
        "ts": None,
    },
    "ha_online": False,
    "boot_time": time.time(),
    "logs": [],
}

# ─── Background: HA health check ────────────────────────────────────
def check_ha():
    while True:
        try:
            r = requests.get(
                f"{HA_URL}/api/",
                headers={"Authorization": f"Bearer {HA_TOKEN}"},
                timeout=5
            )
            state["ha_online"] = (r.status_code == 200)
        except Exception:
            state["ha_online"] = False
        time.sleep(30)


def fetch_ha_entities():
    """Pull relevant HA entities for dashboard."""
    if not HA_TOKEN:
        return
    try:
        r = requests.get(
            f"{HA_URL}/api/states",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            timeout=10
        )
        if r.status_code != 200:
            return
        entities = {e["entity_id"]: e for e in r.json()}

        # Threat level
        threat_map = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}
        threat_ent = entities.get("input_select.s25_threat_level")
        if threat_ent:
            state["threat_level"] = threat_map.get(
                threat_ent["state"].upper(), 0
            )

        # ARKON signal
        for eid in ["sensor.arkon5_signal", "input_text.arkon5_signal"]:
            sig_ent = entities.get(eid)
            if sig_ent:
                try:
                    sig = json.loads(sig_ent["state"])
                    state["signal"].update(sig)
                except Exception:
                    pass
                break

    except Exception:
        pass


def fetch_akt_price():
    """Get AKT price from CoinGecko."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=akash-network&vs_currencies=usd",
            timeout=10
        )
        if r.status_code == 200:
            state["akt_price"] = r.json().get(
                "akash-network", {}
            ).get("usd", 0)
    except Exception:
        pass


def background_tasks():
    """Run periodic background fetches."""
    while True:
        fetch_ha_entities()
        fetch_akt_price()
        time.sleep(60)


# ─── Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(
        HTML,
        version=VERSION,
        build_date=BUILD_DATE,
        ha_url=HA_URL,
    )


@app.route("/api/status")
def api_status():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
    except ImportError:
        cpu, mem = 0.0, 0.0

    return jsonify({
        "ok":           True,
        "version":      VERSION,
        "uptime":       int(time.time() - state["boot_time"]),
        "threat_level": state["threat_level"],
        "signal":       state["signal"],
        "ha_online":    state["ha_online"],
        "cpu":          cpu,
        "memory":       mem,
        "akt_price":    state.get("akt_price", 0),
    })


@app.route("/api/signal", methods=["POST"])
def api_signal():
    """Receive signal from ARKON-5 / HA webhook."""
    from flask import request
    data = request.json or {}
    state["signal"].update({
        "action":     data.get("action"),
        "symbol":     data.get("symbol"),
        "confidence": data.get("confidence", 0),
        "price":      data.get("price", 0),
        "ts":         datetime.utcnow().isoformat(),
    })
    return jsonify({"ok": True})


@app.route("/api/threat", methods=["POST"])
def api_threat():
    """Update threat level."""
    from flask import request
    level = request.json.get("level", 0)
    state["threat_level"] = int(level)
    return jsonify({"ok": True})


@app.route("/api/kill-switch", methods=["POST"])
def api_kill_switch():
    """Emergency kill switch endpoint."""
    state["threat_level"] = 3
    state["logs"].append({
        "ts": datetime.utcnow().isoformat(),
        "event": "KILL_SWITCH",
        "operator": "cockpit_ui"
    })
    return jsonify({"ok": True, "message": "Kill switch activated"})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": VERSION})


# ─── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Register COMET bridge routes
    if _comet_routes_registered:
        register_comet_routes(app, state)
        print("✅ COMET bridge routes registered")
    else:
        print("⚠️  COMET bridge not available (comet_bridge.py missing)")

    # Start background threads
    threading.Thread(target=check_ha,         daemon=True).start()
    threading.Thread(target=background_tasks, daemon=True).start()

    print(f"""
╔══════════════════════════════════════════╗
║   S25 LUMIÈRE — Cockpit v{VERSION}          ║
║   Port:    {PORT}                           ║
║   HA URL:  {HA_URL[:30]}...  ║
║   Mode:    {'LIVE' if HA_TOKEN else 'DEMO (no HA token)'}                      ║
╚══════════════════════════════════════════╝
""")

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        threaded=True,
    )
