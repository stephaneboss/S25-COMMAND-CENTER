'''
S25 Lumiere -- Agent Loop Backend v2.1
======================================
Boucle calme de collecte automatique -- ZERO API PAYANTE.
Sources gratuites: CoinGecko (+ MEXC fallback), Fear&Greed, Reddit RSS.
Analyse IA: Merlin (Gemini) -- validateur/synthetiseur du command center, pas cerveau principal.

Collecte en boucle -> filtre -> log -> push Cockpit -> agents notifies.

Schedule:
  Toutes les 5 min  -> Prix crypto (CoinGecko, fallback MEXC)
  Toutes les 15 min -> Fear & Greed Index
  Toutes les 30 min -> Reddit sentiment (top posts)
  Toutes les 60 min -> Rapport complet Merlin/Gemini (cerveau S25)

Changelog v2.1:
  - Fix #1: CoinGecko key + MEXC fallback + alerte prix stale
  - Fix #2: Startup health check cockpit (fail fast si COCKPIT_URL invalide)
  - Fix #3: Stale prices tracker (alerte si CoinGecko mort > 10 min)
'''

import os
import time
import logging
import threading
import requests
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LOOP] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/agent_loop.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

COCKPIT_URL    = os.getenv("COCKPIT_URL", "http://localhost:7777")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_URL     = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
OLLAMA_URL     = os.getenv("OLLAMA_URL", "http://10.0.0.202:11434")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llama3:latest")
# Fix #1 -- CoinGecko optional API key (demo key gratuit sur coingecko.com)
COINGECKO_KEY  = os.getenv("COINGECKO_KEY", "")
# Fix #3 -- Stale prices: timestamp de la derniere collecte reussie
_last_price_fetch_ok: float = 0.0
PRICE_STALE_WARN_SEC = 600  # alerte si CoinGecko mort > 10 min

PRICE_CHANGE_WARN     = 3.0
PRICE_CHANGE_ALERT    = 7.0
PRICE_CHANGE_CRITICAL = 15.0
FG_FEAR_WARN     = 25
FG_GREED_WARN    = 75

PAIRS = ["bitcoin", "ethereum", "akash-network", "cosmos"]
PAIRS_LABEL = {
    "bitcoin":      "BTC/USDT",
    "ethereum":     "ETH/USDT",
    "akash-network": "AKT/USDT",
    "cosmos":       "ATOM/USDT",
}
_last_prices: dict = {}
_loop_stats = {
    "cycles":        0,
    "intel_pushed":  0,
    "alerts_raised": 0,
    "started":       datetime.now(timezone.utc).isoformat(),
}

def check_cockpit_health() -> bool:
    """Fix #2 -- Verifie que le cockpit est accessible au demarrage.
    Log une erreur claire si COCKPIT_URL pointe sur localhost alors qu'on est sur DELL-LINUX."""
    try:
        r = requests.get(f"{COCKPIT_URL}/api/health", timeout=5)
        if r.status_code == 200:
            log.info(f"Cockpit OK: {COCKPIT_URL}")
            return True
        log.error(f"Cockpit repond {r.status_code} sur {COCKPIT_URL}")
    except Exception as e:
        log.error(
            f"Cockpit INACCESSIBLE: {COCKPIT_URL} -- {e}\n"
            f"  Si tu tournes sur DELL-LINUX, set: COCKPIT_URL=<URL_AKASH_COCKPIT>\n"
            f"  Exemple: COCKPIT_URL=http://uoqlngdqqlc29fhg8l78qt80d8.ingress.akashprovid.com"
        )
    return False


def push_intel(source: str, summary: str, level: str = "INFO", details: str = "") -> bool:
    payload = {
        "source":  source,
        "summary": summary[:500],
        "level":   level,
        "details": details,
    }
    try:
        r = requests.post(f"{COCKPIT_URL}/api/intel", json=payload, timeout=5)
        if r.status_code == 200:
            _loop_stats["intel_pushed"] += 1
            if level in ("ALERT", "CRITICAL"):
                _loop_stats["alerts_raised"] += 1
            return True
    except Exception as e:
        log.warning(f"push_intel error: {e}")
    return False


def push_signal(action: str, symbol: str, confidence: float, price: float, reason: str) -> bool:
    payload = {
        "action":     action,
        "symbol":     symbol,
        "confidence": round(confidence, 3),
        "price":      price,
        "reason":     reason,
        "source":     "AGENT_LOOP",
    }
    try:
        r = requests.post(f"{COCKPIT_URL}/api/signal", json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        log.warning(f"push_signal error: {e}")
    return False


def _fetch_prices_mexc_fallback() -> dict:
    """Fallback MEXC public ticker -- aucune auth requise.
    Retourne un dict au meme format que CoinGecko pour BTC/ETH/AKT/ATOM."""
    MEXC_PAIRS = {
        "bitcoin":       "BTCUSDT",
        "ethereum":      "ETHUSDT",
        "akash-network": "AKTUSDT",
        "cosmos":        "ATOMUSDT",
    }
    result = {}
    try:
        symbols = list(MEXC_PAIRS.values())
        r = requests.get(
            "https://api.mexc.com/api/v3/ticker/24hr",
            params={"symbols": str(symbols).replace("'", '"').replace(" ", "")},
            timeout=10,
            headers={"Accept": "application/json"},
        )
        if r.status_code == 200:
            data = r.json() if isinstance(r.json(), list) else []
            by_symbol = {d["symbol"]: d for d in data}
            for coin_id, sym in MEXC_PAIRS.items():
                ticker = by_symbol.get(sym, {})
                if ticker:
                    price = float(ticker.get("lastPrice", 0) or 0)
                    change = float(ticker.get("priceChangePercent", 0) or 0)
                    if price > 0:
                        result[coin_id] = {"usd": price, "usd_24h_change": change}
    except Exception as e:
        log.warning(f"MEXC fallback error: {e}")
    return result


def fetch_prices() -> dict:
    """Prix via CoinGecko (primaire) avec fallback automatique sur MEXC.
    Fix #1: support COINGECKO_KEY + alerte stale + fallback."""
    global _last_price_fetch_ok
    ids = ",".join(PAIRS)
    headers = {"Accept": "application/json"}
    if COINGECKO_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_KEY
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    )
    try:
        r = requests.get(url, timeout=10, headers=headers)
        if r.status_code == 200:
            _last_price_fetch_ok = time.time()
            return r.json()
        elif r.status_code == 429:
            log.warning("CoinGecko rate-limited (429) -- bascule MEXC fallback")
        else:
            log.warning(f"CoinGecko HTTP {r.status_code} -- bascule MEXC fallback")
    except Exception as e:
        log.warning(f"CoinGecko error: {e} -- bascule MEXC fallback")

    # Fallback MEXC
    data = _fetch_prices_mexc_fallback()
    if data:
        _last_price_fetch_ok = time.time()
        log.info("Prices via MEXC fallback OK")
        return data

    # Verifier si les prix sont stale (Fix #3)
    if _last_price_fetch_ok > 0:
        stale_sec = time.time() - _last_price_fetch_ok
        if stale_sec > PRICE_STALE_WARN_SEC:
            push_intel(
                "PRICE_WATCH",
                f"Prix stale depuis {int(stale_sec/60)} min -- CoinGecko ET MEXC hors ligne",
                "ALERT",
                "Verifier connectivite reseau du serveur",
            )
    return {}


def check_prices():
    """Compare prix vs derniere valeur connue -- push si mouvement significatif."""
    data = fetch_prices()
    if not data:
        log.warning("CoinGecko: no data")
        return
    for coin_id in PAIRS:
        coin = data.get(coin_id, {})
        price    = coin.get("usd", 0)
        change24 = coin.get("usd_24h_change", 0.0) or 0.0
        label    = PAIRS_LABEL.get(coin_id, coin_id)
        if price == 0:
            continue
        last = _last_prices.get(coin_id, price)
        cycle_change = abs((price - last) / last * 100) if last > 0 else 0
        abs_change = abs(change24)
        direction  = "+" if change24 >= 0 else "-"
        if abs_change >= PRICE_CHANGE_CRITICAL:
            level = "CRITICAL"
        elif abs_change >= PRICE_CHANGE_ALERT:
            level = "ALERT"
        elif abs_change >= PRICE_CHANGE_WARN:
            level = "WARNING"
        else:
            level = "INFO"
        summary = f"{label} {direction}{abs_change:.1f}% 24h @ ${price:,.2f}"
        if level != "INFO" or cycle_change >= 2.0:
            push_intel("PRICE_WATCH", summary, level,
                       f"24h change: {change24:.2f}% | price: ${price}")
            log.info(f"[{level}] {summary}")
        _last_prices[coin_id] = price
    btc_price = data.get("bitcoin", {}).get("usd", 0)
    log.info(f"Prices checked: BTC=${btc_price:,.0f}")

def check_fear_greed():
    try:
        r = requests.get(
            "https://api.alternative.me/fng/?limit=1",
            timeout=10
        )
        if r.status_code != 200:
            return
        d = r.json()
        entry = d.get("data", [{}])[0]
        value     = int(entry.get("value", 50))
        label_fg  = entry.get("value_classification", "Neutral")
        if value <= FG_FEAR_WARN:
            level   = "WARNING"
            summary = f"Fear & Greed: {value}/100 -- {label_fg} -- Opportunite potentielle"
        elif value >= FG_GREED_WARN:
            level   = "WARNING"
            summary = f"Fear & Greed: {value}/100 -- {label_fg} -- Attention bulle potentielle"
        else:
            level   = "INFO"
            summary = f"Fear & Greed: {value}/100 -- {label_fg}"
        push_intel("FEAR_GREED", summary, level, f"index={value}")
        log.info(f"F&G: {value} ({label_fg}) [{level}]")
    except Exception as e:
        log.warning(f"Fear&Greed error: {e}")


def check_reddit():
    subs = ["CryptoCurrency", "Bitcoin", "AkashNetwork"]
    keywords_bear = ["crash", "dump", "hack", "exploit", "SEC", "ban", "scam", "rug"]
    keywords_bull = ["ATH", "breakout", "bullrun", "moon", "adoption", "ETF"]
    bear_hits = []
    bull_hits = []
    for sub in subs:
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/hot.json?limit=5",
                headers={"User-Agent": "S25-Lumiere-Bot/1.0"},
                timeout=10,
            )
            if r.status_code != 200:
                continue
            posts = r.json().get("data", {}).get("children", [])
            for p in posts:
                title = p.get("data", {}).get("title", "").lower()
                for kw in keywords_bear:
                    if kw.lower() in title:
                        bear_hits.append(f"r/{sub}: {title[:60]}")
                for kw in keywords_bull:
                    if kw.lower() in title:
                        bull_hits.append(f"r/{sub}: {title[:60]}")
        except Exception as e:
            log.warning(f"Reddit r/{sub} error: {e}")
    if bear_hits:
        level = "ALERT" if len(bear_hits) >= 3 else "WARNING"
        push_intel("REDDIT_SENTIMENT", f"Sentiment BEAR: {len(bear_hits)} signaux negatifs",
                   level, " | ".join(bear_hits[:3]))
        log.warning(f"Reddit BEAR signals: {len(bear_hits)}")
    if bull_hits:
        push_intel("REDDIT_SENTIMENT", f"Sentiment BULL: {len(bull_hits)} signaux positifs",
                   "INFO", " | ".join(bull_hits[:3]))
        log.info(f"Reddit BULL signals: {len(bull_hits)}")
    if not bear_hits and not bull_hits:
        log.info("Reddit: no significant signals")

def merlin_analyze(prompt: str) -> str:
    """Call Merlin (Gemini) -- validateur/synthetiseur du command center."""
    if not GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY non set -- Merlin offline")
        return ""
    try:
        r = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        if r.status_code == 200:
            candidates = r.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
        else:
            log.warning(f"Merlin API error: {r.status_code} {r.text[:100]}")
    except Exception as e:
        log.warning(f"Merlin error: {e}")
    return ""


def ollama_analyze(prompt: str) -> str:
    """Fallback IA local -- Ollama sur DELL-LINUX (10.0.0.202:11434).
    Active automatiquement quand Gemini est offline ou GEMINI_API_KEY absent."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        if r.status_code == 200:
            return r.json().get("response", "").strip()
        else:
            log.warning(f"Ollama error: {r.status_code}")
    except Exception as e:
        log.warning(f"Ollama error: {e}")
    return ""


def hourly_merlin_report():
    """Rapport horaire via Merlin (Gemini) -- synthese externe pour le command center."""
    prices = fetch_prices()
    btc        = prices.get("bitcoin",       {}).get("usd", 0)
    btc_change = prices.get("bitcoin",       {}).get("usd_24h_change", 0)
    eth        = prices.get("ethereum",      {}).get("usd", 0)
    akt        = prices.get("akash-network", {}).get("usd", 0)
    atom       = prices.get("cosmos",        {}).get("usd", 0)

    prompt = f"""Tu es MERLIN, analyste senior du systeme S25 Lumiere (trading crypto multi-agent).
Analyse le marche en 3 lignes max:

BTC: ${btc:,.0f} ({btc_change:+.1f}% 24h)
ETH: ${eth:,.2f}
AKT: ${akt:,.4f}
ATOM: ${atom:,.3f}

Donne: 1) sentiment global (BULL/BEAR/NEUTRE) 2) meilleure opportunite 3) signal (BUY/HOLD/SELL) + asset + raison courte.
Format: SENTIMENT | OPPORTUNITE | SIGNAL"""

    analysis = merlin_analyze(prompt)
    if analysis:
        push_intel("MERLIN_GEMINI", analysis[:400], "INFO", f"model={GEMINI_MODEL}")
        log.info(f"Merlin report: {analysis[:100]}...")
    else:
        log.info("Merlin non disponible -- tentative Ollama fallback (DELL-LINUX)...")
        analysis = ollama_analyze(prompt)
        if analysis:
            push_intel("OLLAMA_LOCAL", analysis[:400], "INFO", f"model={OLLAMA_MODEL}")
            log.info(f"Ollama report: {analysis[:100]}...")
        else:
            log.info("Ollama non disponible -- rapport horaire skipped")


class AgentLoop:
    def __init__(self):
        self._stop = threading.Event()
        self._t5   = 0    # last 5-min run
        self._t15  = 0    # last 15-min run
        self._t30  = 0    # last 30-min run
        self._t60  = 0    # last 60-min run

    def stop(self):
        self._stop.set()
        log.info("AgentLoop stopping...")

    def run(self):
        log.info("Agent Loop demarre -- boucle calme toutes les 60s")
        # Fix #2 -- Verifier cockpit au demarrage (fail-fast avec message clair)
        if not check_cockpit_health():
            log.warning("Cockpit non accessible -- les intel seront perdus jusqu'a reconnexion")
        push_intel("AGENT_LOOP", "Agent Loop demarre -- surveillance active", "INFO")
        while not self._stop.is_set():
            now = time.time()
            _loop_stats["cycles"] += 1
            try:
                if now - self._t5 >= 300:
                    log.info("-- Cycle 5min: check prix")
                    check_prices()
                    self._t5 = now
                if now - self._t15 >= 900:
                    log.info("-- Cycle 15min: Fear & Greed")
                    check_fear_greed()
                    self._t15 = now
                if now - self._t30 >= 1800:
                    log.info("-- Cycle 30min: Reddit sentiment")
                    check_reddit()
                    self._t30 = now
                if now - self._t60 >= 3600:
                    log.info("-- Cycle 60min: Merlin analyse")
                    hourly_merlin_report()
                    self._t60 = now
            except Exception as e:
                log.error(f"Loop cycle error: {e}")
                push_intel("AGENT_LOOP", f"Erreur cycle: {str(e)[:100]}", "WARNING")
            self._stop.wait(60)
        log.info("Agent Loop arrete proprement")

def register_loop_routes(app, loop: AgentLoop):
    from flask import jsonify as _j

    @app.route("/api/loop/status")
    def loop_status():
        return _j({
            "ok":     True,
            "stats":  _loop_stats,
            "prices": {
                PAIRS_LABEL.get(k, k): v
                for k, v in _last_prices.items()
            },
        })

    @app.route("/api/loop/force-cycle", methods=["POST"])
    def force_cycle():
        """Force un cycle immediat (pour tests)."""
        threading.Thread(target=check_prices,    daemon=True).start()
        threading.Thread(target=check_fear_greed, daemon=True).start()
        return _j({"ok": True, "message": "Cycle force lance"})

    log.info("Loop routes enregistrees")


if __name__ == "__main__":
    import signal
    loop = AgentLoop()

    def handle_signal(sig, frame):
        loop.stop()

    signal.signal(signal.SIGINT,  handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log.info("""
+==========================================+
|  S25 LUMIERE -- Agent Loop v2.0          |
|  Sources: CoinGecko + F&G + Reddit       |
|  AI Cerveau: MERLIN (Gemini)             |
|  Sentinel: DELL-Linux (watchdog only)    |
+==========================================+
    """)

    loop.run()
