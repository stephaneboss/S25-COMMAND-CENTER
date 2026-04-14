#!/usr/bin/env python3
"""
ninja_routes.py -- S25 Lumiere Routes Ninja (100% Gratuites)
Agregateur de donnees crypto ZERO cout
Sources: CoinGecko, Fear&Greed, Reddit, DeFiLlama, Blockchair
"""

import requests
import logging
from datetime import datetime, timezone

log = logging.getLogger('ninja_routes')

# --- COINGECKO ---

# ── Simple TTL cache (avoids CoinGecko rate limits) ────────────
import time as _time
_CACHE: dict = {}
_TTL_DEFAULT = 60

def _cache_get(key: str, ttl: int = _TTL_DEFAULT):
    v = _CACHE.get(key)
    if not v:
        return None
    ts, data = v
    if (_time.time() - ts) > ttl:
        return None
    return data

def _cache_set(key: str, data) -> None:
    _CACHE[key] = (_time.time(), data)


# Map CoinGecko ids to Binance symbols for fallback
_BINANCE_MAP = {
    'bitcoin': 'BTCUSDT', 'ethereum': 'ETHUSDT', 'solana': 'SOLUSDT',
    'dogecoin': 'DOGEUSDT', 'cosmos': 'ATOMUSDT', 'akash-network': 'AKTUSDT',
    'chainlink': 'LINKUSDT', 'uniswap': 'UNIUSDT', 'aave': 'AAVEUSDT',
    'maker': 'MKRUSDT', 'injective-protocol': 'INJUSDT',
}

def _binance_fallback(symbols: list) -> dict:
    """Fallback to Binance public 24hr ticker (no rate limit for public)."""
    out = {}
    try:
        r = requests.get('https://api.binance.com/api/v3/ticker/24hr', timeout=8)
        if r.status_code != 200:
            return out
        by_sym = {t['symbol']: t for t in r.json()}
        for cg_id in symbols:
            bs = _BINANCE_MAP.get(cg_id)
            if not bs or bs not in by_sym:
                continue
            t = by_sym[bs]
            out[cg_id] = {
                'usd': float(t['lastPrice']),
                'usd_24h_change': float(t['priceChangePercent']),
                'usd_24h_vol': float(t['quoteVolume']),
            }
    except Exception as e:
        log.warning(f'Binance fallback error: {e}')
    return out

def get_prices(symbols: list = None) -> dict:
    """Prix spot en USD avec cache TTL 60s + CoinGecko puis Binance fallback."""
    if symbols is None:
        symbols = ['bitcoin', 'ethereum', 'solana', 'injective-protocol']
    key = 'prices:' + ','.join(sorted(symbols))
    cached = _cache_get(key)
    if cached:
        return cached
    # 1. Try CoinGecko
    try:
        r = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={
                'ids': ','.join(symbols),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
            },
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            if data:
                _cache_set(key, data)
                return data
        else:
            log.warning(f'CoinGecko HTTP {r.status_code}, falling back to Binance')
    except Exception as e:
        log.warning(f'CoinGecko prices error: {e}, falling back to Binance')
    # 2. Binance fallback
    data = _binance_fallback(symbols)
    if data:
        _cache_set(key, data)
    return data


def get_trending() -> list:
    """Top 7 coins trending sur CoinGecko -- gratuit."""
    try:
        r = requests.get('https://api.coingecko.com/api/v3/search/trending', timeout=10)
        if r.status_code == 200:
            return [
                {'symbol': c['item']['symbol'], 'name': c['item']['name'], 'rank': i+1}
                for i, c in enumerate(r.json().get('coins', []))
            ]
    except Exception as e:
        log.warning(f'CoinGecko trending error: {e}')
    return []


def get_global_market() -> dict:
    """Donnees globales marche crypto -- gratuit."""
    try:
        r = requests.get('https://api.coingecko.com/api/v3/global', timeout=10)
        if r.status_code == 200:
            d = r.json()['data']
            return {
                'total_market_cap_usd': d['total_market_cap']['usd'],
                'btc_dominance': d['market_cap_percentage']['btc'],
                'eth_dominance': d['market_cap_percentage'].get('eth'),
                'active_cryptos': d['active_cryptocurrencies'],
                'market_cap_change_24h': d['market_cap_change_percentage_24h_usd'],
            }
    except Exception as e:
        log.warning(f'CoinGecko global error: {e}')
    return {}


# --- FEAR & GREED ---

def get_fear_greed(limit: int = 7) -> list:
    """Historique Fear & Greed -- alternative.me gratuit."""
    try:
        r = requests.get(f'https://api.alternative.me/fng/?limit={limit}', timeout=10)
        if r.status_code == 200:
            return [
                {'value': int(d['value']), 'label': d['value_classification'], 'date': d['timestamp']}
                for d in r.json()['data']
            ]
    except Exception as e:
        log.warning(f'Fear&Greed error: {e}')
    return []


# --- REDDIT ---

def get_reddit_hot(subreddit: str, limit: int = 25) -> list:
    """Posts hot Reddit -- JSON API gratuit, pas de cle."""
    try:
        r = requests.get(
            f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}',
            headers={'User-Agent': 'S25-NinjaRoutes/1.0'},
            timeout=10,
        )
        if r.status_code == 200:
            return [
                {
                    'title': p['data']['title'],
                    'score': p['data']['score'],
                    'comments': p['data']['num_comments'],
                    'url': f"https://reddit.com{p['data']['permalink']}",
                }
                for p in r.json()['data']['children']
            ]
    except Exception as e:
        log.warning(f'Reddit r/{subreddit} error: {e}')
    return []


# --- DEFI LLAMA ---

def get_defi_tvl_top(limit: int = 10) -> list:
    """Top protocols par TVL -- DeFiLlama gratuit."""
    try:
        r = requests.get('https://api.llama.fi/protocols', timeout=15)
        if r.status_code == 200:
            protocols = sorted(r.json(), key=lambda x: x.get('tvl', 0), reverse=True)
            return [
                {'name': p['name'], 'tvl_usd': p.get('tvl'), 'chain': p.get('chain', 'multi')}
                for p in protocols[:limit]
            ]
    except Exception as e:
        log.warning(f'DeFiLlama error: {e}')
    return []


def get_chain_tvl(chain: str = 'Ethereum') -> dict:
    """TVL d'une chain -- DeFiLlama gratuit."""
    try:
        r = requests.get('https://api.llama.fi/v2/chains', timeout=10)
        if r.status_code == 200:
            for c in r.json():
                if c['name'].lower() == chain.lower():
                    return {'chain': c['name'], 'tvl_usd': c.get('tvl')}
    except Exception as e:
        log.warning(f'DeFiLlama chain error: {e}')
    return {}


# --- COMPOUND INTEL ---

def get_full_intel_snapshot() -> dict:
    """Snapshot complet -- toutes les sources gratuites en 1 appel."""
    prices = get_prices()
    fg = get_fear_greed(limit=1)
    trending = get_trending()
    global_data = get_global_market()

    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'prices': prices,
        'fear_greed': fg[0] if fg else {},
        'trending': trending[:5],
        'global': global_data,
        'source': 'ninja_routes_v1',
        'cost': '$0.00',
    }


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    print('=== S25 Ninja Routes -- Snapshot ===')
    snapshot = get_full_intel_snapshot()
    print(json.dumps(snapshot, indent=2))