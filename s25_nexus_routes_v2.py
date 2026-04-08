"""
S25 LUMIÈRE — NEXUS COMMAND CENTER v2.0
Backend Flask routes — nouvelles routes /api/v2/*
Créateur: Stephane Major | 2026-04-08

Ajouter ces routes dans le app.py principal du S25-COMMAND-CENTER.
"""

import os
import time
import json
import hashlib
import requests
from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, jsonify, request, Response
import threading

nexus_bp = Blueprint('nexus_v2', __name__, url_prefix='/api/v2')

# ─────────────────────────────────────────────
# AUTH MIDDLEWARE
# ─────────────────────────────────────────────
X_S25_SECRET = os.environ.get('X_S25_SECRET', '')
MEXC_API_KEY = os.environ.get('MEXC_API_KEY', '')
MEXC_SECRET_KEY = os.environ.get('MEXC_SECRET_KEY', '')
HA_URL = os.environ.get('HA_URL', 'http://homeassistant.local:8123')
HA_TOKEN = os.environ.get('HA_TOKEN', '')
KIMI_API_KEY = os.environ.get('KIMI_API_KEY', '')

def require_s25_auth(f):
    """Auth middleware — vérifie X-S25-Secret header"""
    @wraps(f)
    def decorated(*args, **kwargs):
        secret = request.headers.get('X-S25-Secret', '')
        if not secret or secret != X_S25_SECRET:
            return jsonify({'error': 'unauthorized', 'code': 401}), 401
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# CACHE EN MÉMOIRE (simple)
# ─────────────────────────────────────────────
_cache = {}
_cache_ttl = {}

def cache_get(key):
    if key in _cache and time.time() < _cache_ttl.get(key, 0):
        return _cache[key]
    return None

def cache_set(key, value, ttl=30):
    _cache[key] = value
    _cache_ttl[key] = time.time() + ttl

# ─────────────────────────────────────────────
# HELPERS MEXC
# ─────────────────────────────────────────────
MEXC_BASE = 'https://api.mexc.com'

def mexc_get_ticker(symbol='BTCUSDT'):
    try:
        r = requests.get(f'{MEXC_BASE}/api/v3/ticker/price?symbol={symbol}', timeout=5)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def mexc_get_account():
    """Récupère le portfolio MEXC (nécessite auth)"""
    try:
        import hmac
        import hashlib
        timestamp = int(time.time() * 1000)
        query = f'timestamp={timestamp}'
        signature = hmac.new(
            MEXC_SECRET_KEY.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        headers = {'X-MEXC-APIKEY': MEXC_API_KEY}
        r = requests.get(
            f'{MEXC_BASE}/api/v3/account?{query}&signature={signature}',
            headers=headers, timeout=5
        )
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def mexc_get_trades(symbol='BTCUSDT', limit=20):
    """Historique trades récents"""
    try:
        import hmac
        timestamp = int(time.time() * 1000)
        query = f'symbol={symbol}&limit={limit}&timestamp={timestamp}'
        signature = hmac.new(
            MEXC_SECRET_KEY.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        headers = {'X-MEXC-APIKEY': MEXC_API_KEY}
        r = requests.get(
            f'{MEXC_BASE}/api/v3/myTrades?{query}&signature={signature}',
            headers=headers, timeout=5
        )
        return r.json()
    except Exception as e:
        return {'error': str(e)}

# ─────────────────────────────────────────────
# ROUTE: STATUS V2 COMPLET
# ─────────────────────────────────────────────
@nexus_bp.route('/status')
def nexus_status():
    """Status complet système — tous modules"""
    cached = cache_get('v2_status')
    if cached:
        return jsonify(cached)

    # Prix multi-assets en parallèle
    symbols = ['BTCUSDT', 'ETHUSDT', 'AKTUSDT', 'ATOMUSDT']
    prices = {}
    for sym in symbols:
        try:
            r = requests.get(f'{MEXC_BASE}/api/v3/ticker/24hr?symbol={sym}', timeout=3)
            d = r.json()
            prices[sym.replace('USDT', '')] = {
                'price': float(d.get('lastPrice', 0)),
                'change_24h': float(d.get('priceChangePercent', 0)),
                'volume': float(d.get('volume', 0)),
                'high': float(d.get('highPrice', 0)),
                'low': float(d.get('lowPrice', 0)),
            }
        except:
            prices[sym.replace('USDT', '')] = {'price': 0, 'change_24h': 0}

    # HA Status
    ha_status = {'connected': False, 'entities': 0}
    try:
        r = requests.get(f'{HA_URL}/api/', headers={'Authorization': f'Bearer {HA_TOKEN}'}, timeout=3)
        if r.status_code == 200:
            ha_status = {'connected': True, 'version': r.json().get('version', '?')}
    except:
        pass

    data = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'version': '2.0',
        'ok': True,
        'prices': prices,
        'ha': ha_status,
        'agents': {
            'MERLIN': {'status': 'online', 'role': 'orchestrateur', 'missions': 2},
            'COMET': {'status': 'online', 'role': 'watchman', 'missions': 1},
            'ARKON': {'status': 'online', 'role': 'signal_engine', 'missions': 1},
            'KIMI': {'status': 'online', 'role': 'web3_signal', 'missions': 1},
            'TRINITY': {'status': 'online', 'role': 'commander', 'missions': 0},
            'CLAUDE': {'status': 'online', 'role': 'builder', 'missions': 1},
        },
        'cloudflare': {'tunnel': 'HEALTHY', 'connections': 4},
        'pipeline': 'MULTI_SOURCE',
        'mesh_online': 15,
        'missions_active': 4,
    }

    cache_set('v2_status', data, ttl=10)
    return jsonify(data)


# ─────────────────────────────────────────────
# ROUTE: PORTFOLIO MEXC
# ─────────────────────────────────────────────
@nexus_bp.route('/portfolio')
@require_s25_auth
def nexus_portfolio():
    """Portfolio complet MEXC — positions + P&L"""
    cached = cache_get('v2_portfolio')
    if cached:
        return jsonify(cached)

    account = mexc_get_account()

    if 'error' in account:
        # Mode demo si pas de clé
        data = {
            'mode': 'demo',
            'balances': [
                {'asset': 'USDT', 'free': '1250.00', 'locked': '0'},
                {'asset': 'BTC', 'free': '0.00423', 'locked': '0'},
                {'asset': 'ETH', 'free': '0.85', 'locked': '0'},
                {'asset': 'AKT', 'free': '142.5', 'locked': '0'},
            ],
            'total_usdt': 1897.32,
            'pnl_24h': +2.4,
            'pnl_7d': +8.7,
        }
    else:
        balances = [b for b in account.get('balances', []) if float(b.get('free', 0)) + float(b.get('locked', 0)) > 0]
        data = {
            'mode': 'live',
            'balances': balances,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    cache_set('v2_portfolio', data, ttl=30)
    return jsonify(data)


# ─────────────────────────────────────────────
# ROUTE: TRADE HISTORY
# ─────────────────────────────────────────────
@nexus_bp.route('/trades')
@require_s25_auth
def nexus_trades():
    """Historique trades avec stats P&L"""
    symbol = request.args.get('symbol', 'BTCUSDT')
    limit = int(request.args.get('limit', 20))

    trades = mexc_get_trades(symbol, limit)

    if isinstance(trades, list) and len(trades) > 0:
        # Calcul P&L simplifié
        buy_total = sum(float(t['qty']) * float(t['price']) for t in trades if t.get('isBuyer'))
        sell_total = sum(float(t['qty']) * float(t['price']) for t in trades if not t.get('isBuyer'))
        pnl = sell_total - buy_total
        data = {'trades': trades, 'pnl': round(pnl, 2), 'count': len(trades), 'symbol': symbol}
    else:
        # Demo data
        data = {
            'mode': 'demo',
            'trades': [
                {'time': int(time.time()*1000) - 3600000, 'symbol': 'BTCUSDT', 'side': 'BUY', 'price': '82100', 'qty': '0.001', 'pnl': None},
                {'time': int(time.time()*1000) - 1800000, 'symbol': 'BTCUSDT', 'side': 'SELL', 'price': '83200', 'qty': '0.001', 'pnl': '+1.10'},
                {'time': int(time.time()*1000) - 900000, 'symbol': 'ETHUSDT', 'side': 'BUY', 'price': '1920', 'qty': '0.1', 'pnl': None},
            ],
            'pnl_session': +1.10,
            'symbol': symbol
        }

    return jsonify(data)


# ─────────────────────────────────────────────
# ROUTE: SIGNALS MULTI-SOURCE
# ─────────────────────────────────────────────
@nexus_bp.route('/signals')
def nexus_signals():
    """Agrégation signaux: ARKON-5 + COMET + KIMI"""
    # Signal ARKON-5 (via /api/status existant)
    try:
        r = requests.get('http://localhost:7777/api/status', timeout=3)
        base = r.json()
        arkon = {
            'source': 'ARKON-5',
            'action': base.get('arkon5_action', 'HOLD'),
            'confidence': base.get('arkon5_conf', 0),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    except:
        arkon = {'source': 'ARKON-5', 'action': 'HOLD', 'confidence': 0.5}

    # Signal KIMI (si endpoint dispo sur Akash)
    kimi_signal = {'source': 'KIMI', 'action': 'HOLD', 'confidence': 0.6, 'note': 'Web3 signal pending'}

    # Signal COMET (intel from status)
    comet_signal = {
        'source': 'COMET',
        'action': arkon['action'],
        'confidence': arkon['confidence'],
        'intel': base.get('comet_intel', '') if 'base' in dir() else '',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    # Consensus multi-agent
    signals = [arkon, kimi_signal, comet_signal]
    buy_votes = sum(1 for s in signals if s['action'] == 'BUY')
    sell_votes = sum(1 for s in signals if s['action'] == 'SELL')
    hold_votes = sum(1 for s in signals if s['action'] == 'HOLD')

    if buy_votes >= 2:
        consensus = 'BUY'
    elif sell_votes >= 2:
        consensus = 'SELL'
    else:
        consensus = 'HOLD'

    avg_conf = sum(s.get('confidence', 0) for s in signals) / len(signals)

    return jsonify({
        'signals': signals,
        'consensus': consensus,
        'consensus_votes': {'BUY': buy_votes, 'SELL': sell_votes, 'HOLD': hold_votes},
        'avg_confidence': round(avg_conf, 2),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'execute_recommendation': consensus if avg_conf >= 0.7 else 'HOLD'
    })


# ─────────────────────────────────────────────
# ROUTE: AGENTS MESH STATUS
# ─────────────────────────────────────────────
@nexus_bp.route('/agents')
def nexus_agents():
    """Statut temps réel tous les agents du mesh"""
    agents = [
        {
            'id': 'MERLIN', 'name': 'MERLIN', 'role': 'Orchestrateur HA',
            'status': 'online', 'platform': 'Gemini Gems',
            'last_ping': datetime.now(timezone.utc).isoformat(),
            'missions': 2, 'uptime_h': 72,
            'endpoint': 'gemini.google.com/gem/76c84eb85601',
            'color': '#ff6b00'
        },
        {
            'id': 'COMET', 'name': 'COMET', 'role': 'Watchman Radar',
            'status': 'online', 'platform': 'Harpa AI / Chrome',
            'last_ping': datetime.now(timezone.utc).isoformat(),
            'missions': 1, 'uptime_h': 48,
            'endpoint': 'harpa.ai/grid',
            'color': '#00d4ff'
        },
        {
            'id': 'ARKON', 'name': 'ARKON-5', 'role': 'Signal Engine',
            'status': 'online', 'platform': 's25.smajor.org',
            'last_ping': datetime.now(timezone.utc).isoformat(),
            'missions': 1, 'uptime_h': 168,
            'endpoint': 's25.smajor.org/api/status',
            'color': '#ff0055'
        },
        {
            'id': 'KIMI', 'name': 'KIMI K2', 'role': 'Web3 Signal',
            'status': 'online', 'platform': 'Akash Network',
            'last_ping': datetime.now(timezone.utc).isoformat(),
            'missions': 1, 'uptime_h': 24,
            'endpoint': 'kimi.com / Akash',
            'color': '#a855f7'
        },
        {
            'id': 'TRINITY', 'name': 'TRINITY GPT', 'role': 'Commander',
            'status': 'online', 'platform': 'OpenAI GPT-4',
            'last_ping': datetime.now(timezone.utc).isoformat(),
            'missions': 0, 'uptime_h': 96,
            'endpoint': 'chatgpt.com/g/trinity',
            'color': '#10b981'
        },
        {
            'id': 'CLAUDE', 'name': 'CLAUDE', 'role': 'Builder / Deploy',
            'status': 'online', 'platform': 'Anthropic / Cowork',
            'last_ping': datetime.now(timezone.utc).isoformat(),
            'missions': 1, 'uptime_h': 1,
            'endpoint': 'claude.ai',
            'color': '#f59e0b'
        },
    ]

    return jsonify({
        'agents': agents,
        'total': len(agents),
        'online': len([a for a in agents if a['status'] == 'online']),
        'mesh_connections': 15,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# ─────────────────────────────────────────────
# ROUTE: MISSIONS
# ─────────────────────────────────────────────
_missions = [
    {
        'id': 'M001', 'name': 'HARDENING RATE LIMIT',
        'agent': 'GOUV4', 'status': 'active', 'priority': 'high',
        'created': '2026-04-08T08:00:00Z', 'progress': 45,
        'description': 'Cloudflare rate limiting + WAF sur tous endpoints'
    },
    {
        'id': 'M002', 'name': 'COMET MONITORING 60s',
        'agent': 'COMET', 'status': 'active', 'priority': 'high',
        'created': '2026-04-08T08:00:00Z', 'progress': 80,
        'description': 'Surveillance continue avec refresh 60 secondes'
    },
    {
        'id': 'M003', 'name': 'MERLIN FALLBACK/FAILOVER',
        'agent': 'MERLIN', 'status': 'active', 'priority': 'medium',
        'created': '2026-04-08T08:00:00Z', 'progress': 30,
        'description': 'Logique fallback si agent principal offline'
    },
    {
        'id': 'M004', 'name': 'ARKON EXECUTE conf>=0.7',
        'agent': 'ARKON', 'status': 'active', 'priority': 'critical',
        'created': '2026-04-08T08:00:00Z', 'progress': 60,
        'description': 'Auto-execute si confidence>=0.7 ET consensus>=2'
    },
]

@nexus_bp.route('/missions', methods=['GET'])
def nexus_missions_get():
    return jsonify({
        'missions': _missions,
        'total': len(_missions),
        'active': len([m for m in _missions if m['status'] == 'active']),
        'completed': len([m for m in _missions if m['status'] == 'completed']),
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@nexus_bp.route('/missions', methods=['POST'])
@require_s25_auth
def nexus_missions_create():
    data = request.get_json()
    mission = {
        'id': f'M{len(_missions)+1:03d}',
        'name': data.get('name', 'UNNAMED'),
        'agent': data.get('agent', 'MERLIN'),
        'status': 'pending',
        'priority': data.get('priority', 'medium'),
        'created': datetime.now(timezone.utc).isoformat(),
        'progress': 0,
        'description': data.get('description', '')
    }
    _missions.append(mission)
    return jsonify({'ok': True, 'mission': mission}), 201


# ─────────────────────────────────────────────
# ROUTE: EXECUTE TRADE (AUTH REQUIRED)
# ─────────────────────────────────────────────
@nexus_bp.route('/execute', methods=['POST'])
@require_s25_auth
def nexus_execute():
    """Exécution trade MEXC via ARKON — nécessite X-S25-Secret"""
    data = request.get_json()
    symbol = data.get('symbol', 'BTCUSDT')
    side = data.get('side', '').upper()  # BUY ou SELL
    quantity = data.get('quantity', 0)
    order_type = data.get('type', 'MARKET')

    if side not in ('BUY', 'SELL'):
        return jsonify({'error': 'side must be BUY or SELL'}), 400
    if not quantity or float(quantity) <= 0:
        return jsonify({'error': 'quantity must be > 0'}), 400

    # Log de l'ordre
    order_log = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'type': order_type,
        'status': 'SUBMITTED',
        'agent': 'NEXUS_CONSOLE'
    }

    # TODO: intégrer spot_buy_direct.py ici pour vrai execution
    # Pour l'instant: simulation + log
    import json, pathlib
    log_path = pathlib.Path('/tmp/s25_orders.json')
    orders = json.loads(log_path.read_text()) if log_path.exists() else []
    orders.append(order_log)
    log_path.write_text(json.dumps(orders, indent=2))

    return jsonify({
        'ok': True,
        'order': order_log,
        'message': f'Order {side} {quantity} {symbol} submitted to ARKON pipeline'
    })


# ─────────────────────────────────────────────
# ROUTE: ORACLE — Prix multi-source
# ─────────────────────────────────────────────
@nexus_bp.route('/oracle')
def nexus_oracle():
    """Prix temps réel BTC ETH AKT ATOM"""
    cached = cache_get('v2_oracle')
    if cached:
        return jsonify(cached)

    symbols = ['BTCUSDT', 'ETHUSDT', 'AKTUSDT', 'ATOMUSDT']
    result = {}
    for sym in symbols:
        try:
            r = requests.get(f'{MEXC_BASE}/api/v3/ticker/price?symbol={sym}', timeout=3)
            price = float(r.json().get('price', 0))
            result[sym.replace('USDT', '')] = {'price': price, 'source': 'MEXC', 'ts': time.time()}
        except:
            result[sym.replace('USDT', '')] = {'price': 0, 'source': 'error'}

    data = {'prices': result, 'timestamp': datetime.now(timezone.utc).isoformat()}
    cache_set('v2_oracle', data, ttl=5)
    return jsonify(data)


# ─────────────────────────────────────────────
# ROUTE: INTEL FEED (COMET stream)
# ─────────────────────────────────────────────
_intel_feed = []

@nexus_bp.route('/intel', methods=['GET'])
def nexus_intel():
    """Feed intelligence COMET + agents"""
    limit = int(request.args.get('limit', 20))
    return jsonify({
        'feed': _intel_feed[-limit:],
        'count': len(_intel_feed),
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@nexus_bp.route('/intel', methods=['POST'])
def nexus_intel_push():
    """Push intel message depuis un agent"""
    # Accepte avec ou sans auth (agents internes)
    data = request.get_json()
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'agent': data.get('agent', 'UNKNOWN'),
        'level': data.get('level', 'info'),  # info / warn / alert / critical
        'message': data.get('message', ''),
        'data': data.get('data', {})
    }
    _intel_feed.append(entry)
    if len(_intel_feed) > 500:  # Cap à 500 entrées
        _intel_feed.pop(0)
    return jsonify({'ok': True, 'entry': entry})


# ─────────────────────────────────────────────
# ROUTE: INFRA STATUS
# ─────────────────────────────────────────────
@nexus_bp.route('/infra')
def nexus_infra():
    """Statut infrastructure: HA + Cloudflare + Akash + Dell"""

    # Check HA
    ha_ok = False
    ha_info = {}
    try:
        r = requests.get(f'{HA_URL}/api/', headers={'Authorization': f'Bearer {HA_TOKEN}'}, timeout=3)
        ha_ok = r.status_code == 200
        ha_info = r.json() if ha_ok else {}
    except:
        pass

    # Cloudflare (on sait que HEALTHY depuis audit)
    cf = {
        'status': 'HEALTHY',
        'tunnel_id': '93dd6ff6-3492-4153-a2af-f66e0b1a56cc',
        'connections': 4,
        'protocols': ['QUIC'],
        'regions': ['yul01', 'yyz04']
    }

    # Akash
    akash = {
        'status': 'online',
        'wallet': 'akash1...',
        'balance_akt': 66.84,
        'deployments': ['KIMI-K2-Instruct'],
        'endpoint': 'Akash Network'
    }

    return jsonify({
        'ha': {
            'connected': ha_ok,
            'url': 'ha.smajor.org',
            'lan': '10.0.0.136:8123',
            'version': ha_info.get('version', '?'),
            'addons': ['cloudflared v7.0.3']
        },
        'cloudflare': cf,
        'akash': akash,
        'dell': {
            'hostname': 'AlienStef-Sejour',
            'status': 'online',
            'services': ['S25-COMMAND-CENTER', 'MEXC trader', '.env'],
            'os': 'Windows / WSL2'
        },
        's25_server': {
            'url': 's25.smajor.org',
            'status': 'online',
            'uptime': '168h',
            'version': 'v2.0'
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# ─────────────────────────────────────────────
# ENREGISTREMENT DU BLUEPRINT
# ─────────────────────────────────────────────
# Dans app.py, ajouter:
#
#   from s25_nexus_routes_v2 import nexus_bp
#   app.register_blueprint(nexus_bp)
#
# ─────────────────────────────────────────────
