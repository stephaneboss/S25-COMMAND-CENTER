"""
S25 Alert Rules Engine
======================
Declarative rule catalogue for intelligent alerts.

Each rule defines:
- id: stable identifier
- name: human-readable label
- severity: info | warn | critical
- check(metrics): pure function returning bool
- actions: list of dispatch actions ("intel", "ha_notify", "signal")
- cooldown_s: seconds before the same rule can fire again
- signal_payload: payload template when "signal" action is dispatched

Rules are evaluated against a metrics dict assembled from
/api/market/live and /api/system/health internal calls.

Standalone test:
    python3 -m agents.alert_rules
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any, List, Dict, Optional
from datetime import datetime, timezone
import json
import os
import time

ALERT_STATE_FILE = os.environ.get(
    "ALERT_STATE_FILE",
    os.path.join(os.environ.get("MEMORY_DIR", "./memory"), "alert_state.json"),
)


@dataclass
class Rule:
    id: str
    name: str
    severity: str  # info|warn|critical
    description: str
    check: Callable[[Dict[str, Any]], bool]
    actions: List[str] = field(default_factory=list)
    cooldown_s: int = 900
    signal_payload: Optional[Dict[str, Any]] = None

    def serialize(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity,
            "description": self.description,
            "actions": list(self.actions),
            "cooldown_s": self.cooldown_s,
        }


def _get(d: Any, path: str, default=None):
    """Safe nested dict access: _get(m, 'fear_greed.current.value')."""
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


def _disk_pct(m: Dict[str, Any]) -> int:
    raw = _get(m, "disk.pct", "0%") or "0%"
    try:
        return int(str(raw).rstrip("%"))
    except Exception:
        return 0


# ============================================================
# RULE CATALOGUE
# ============================================================

RULES: List[Rule] = [
    # ── MARKET ────────────────────────────────────────────────
    Rule(
        id="market_extreme_fear",
        name="Fear & Greed extreme",
        severity="info",
        description="F&G sous 15 — historiquement zone d'accumulation",
        check=lambda m: (_get(m, "fear_greed.current.value", 50) or 50) < 15,
        actions=["intel", "ha_notify", "signal"],
        cooldown_s=3600,
        signal_payload={
            "action": "BUY",
            "symbol": "BTC/USDT",
            "confidence": 0.72,
            "reason": "Fear & Greed zone extreme — signal contrarian macro",
            "source": "ALERTS",
        },
    ),
    Rule(
        id="market_extreme_greed",
        name="Greed extreme",
        severity="info",
        description="F&G au dessus de 85 — zone de prise de profit",
        check=lambda m: (_get(m, "fear_greed.current.value", 50) or 50) > 85,
        actions=["intel", "ha_notify", "signal"],
        cooldown_s=3600,
        signal_payload={
            "action": "SELL",
            "symbol": "BTC/USDT",
            "confidence": 0.68,
            "reason": "Greed extreme — zone de profit-taking",
            "source": "ALERTS",
        },
    ),
    Rule(
        id="market_btc_pump_24h",
        name="BTC pump 24h",
        severity="warn",
        description="BTC +5% ou plus sur 24h",
        check=lambda m: (_get(m, "prices.bitcoin.change_24h", 0) or 0) >= 5.0,
        actions=["intel", "ha_notify"],
        cooldown_s=1800,
    ),
    Rule(
        id="market_btc_dump_24h",
        name="BTC dump 24h",
        severity="warn",
        description="BTC -5% ou pire sur 24h",
        check=lambda m: (_get(m, "prices.bitcoin.change_24h", 0) or 0) <= -5.0,
        actions=["intel", "ha_notify"],
        cooldown_s=1800,
    ),
    Rule(
        id="market_eth_pump_24h",
        name="ETH pump 24h",
        severity="info",
        description="ETH +5% ou plus sur 24h",
        check=lambda m: (_get(m, "prices.ethereum.change_24h", 0) or 0) >= 5.0,
        actions=["intel"],
        cooldown_s=1800,
    ),
    Rule(
        id="market_doge_pump_24h",
        name="DOGE pump 24h",
        severity="warn",
        description="DOGE +8% ou plus sur 24h (position 1.6M ready)",
        check=lambda m: (_get(m, "prices.dogecoin.change_24h", 0) or 0) >= 8.0,
        actions=["intel", "ha_notify", "signal"],
        cooldown_s=1800,
        signal_payload={
            "action": "SELL",
            "symbol": "DOGE/USDT",
            "confidence": 0.65,
            "reason": "DOGE pump detecte — prise profit sur position 1.6M",
            "source": "ALERTS",
        },
    ),

    # ── INFRA ─────────────────────────────────────────────────
    Rule(
        id="infra_disk_critical",
        name="Disk critique",
        severity="critical",
        description="Disque / au dessus de 85%",
        check=lambda m: _disk_pct(m) >= 85,
        actions=["intel", "ha_notify"],
        cooldown_s=3600,
    ),
    Rule(
        id="infra_disk_warn",
        name="Disk warning",
        severity="warn",
        description="Disque / au dessus de 75%",
        check=lambda m: 75 <= _disk_pct(m) < 85,
        actions=["intel"],
        cooldown_s=7200,
    ),
    Rule(
        id="infra_gpu_hot",
        name="GPU hot",
        severity="warn",
        description="Temperature GPU au dessus de 85 degres",
        check=lambda m: (_get(m, "gpu.temp_c", 0) or 0) >= 85,
        actions=["intel", "ha_notify"],
        cooldown_s=900,
    ),
    Rule(
        id="infra_mesh_degraded",
        name="Mesh degrade",
        severity="warn",
        description="Moins de 12 agents online sur 14",
        check=lambda m: (_get(m, "agents.online", 14) or 14) < 12,
        actions=["intel", "ha_notify"],
        cooldown_s=1800,
    ),
    Rule(
        id="infra_ha_disconnected",
        name="Home Assistant deconnecte",
        severity="critical",
        description="HA bridge ne repond pas",
        check=lambda m: not bool(_get(m, "ha.connected", True)),
        actions=["intel"],
        cooldown_s=600,
    ),
    Rule(
        id="infra_ollama_offline",
        name="Ollama offline",
        severity="warn",
        description="Ollama local ne repond pas",
        check=lambda m: _get(m, "ollama.status") != "online",
        actions=["intel", "ha_notify"],
        cooldown_s=1800,
    ),
    Rule(
        id="infra_cloudflare_down",
        name="Cloudflare tunnel down",
        severity="critical",
        description="Aucun process cloudflared trouve",
        check=lambda m: _get(m, "cloudflare.tunnels") != "running",
        actions=["intel", "ha_notify"],
        cooldown_s=600,
    ),
]


# ============================================================
# STATE + COOLDOWN
# ============================================================

def _load_state() -> dict:
    try:
        with open(ALERT_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"fired": {}}


def _save_state(state: dict) -> None:
    path = ALERT_STATE_FILE
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _cooldown_ok(rule: Rule, state: dict) -> bool:
    last = state.get("fired", {}).get(rule.id, {}).get("last_ts")
    if not last:
        return True
    try:
        last_t = datetime.fromisoformat(last.replace("Z", "+00:00")).timestamp()
    except Exception:
        return True
    return (time.time() - last_t) >= rule.cooldown_s


def _record_fire(rule: Rule, state: dict) -> None:
    state.setdefault("fired", {})
    prev = state["fired"].get(rule.id, {"count": 0})
    prev["last_ts"] = datetime.now(timezone.utc).isoformat()
    prev["count"] = prev.get("count", 0) + 1
    state["fired"][rule.id] = prev


# ============================================================
# EVALUATION ENTRY POINT
# ============================================================

def evaluate_all(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate all rules against the provided metrics snapshot.
    Returns: {evaluated, firing: [Rule dicts], skipped_cooldown: [ids]}
    Does NOT dispatch — the caller is responsible for acting on
    returned firing rules (so we can test the rule engine standalone).
    """
    state = _load_state()
    firing = []
    skipped = []
    errors = []

    for rule in RULES:
        try:
            if not rule.check(metrics):
                continue
        except Exception as e:
            errors.append({"rule": rule.id, "error": str(e)})
            continue
        if not _cooldown_ok(rule, state):
            skipped.append(rule.id)
            continue
        firing.append({
            **rule.serialize(),
            "signal_payload": rule.signal_payload,
        })
        _record_fire(rule, state)

    _save_state(state)
    return {
        "evaluated": len(RULES),
        "firing_count": len(firing),
        "firing": firing,
        "skipped_cooldown": skipped,
        "errors": errors,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def list_rules() -> List[Dict[str, Any]]:
    return [r.serialize() for r in RULES]


def get_state() -> Dict[str, Any]:
    return _load_state()


if __name__ == "__main__":
    # Smoke test with fake metrics reflecting current live data
    fake = {
        "fear_greed": {"current": {"value": 12, "label": "Extreme Fear"}},
        "prices": {
            "bitcoin": {"usd": 75252, "change_24h": 4.56},
            "ethereum": {"usd": 2367, "change_24h": 6.57},
            "dogecoin": {"usd": 0.096, "change_24h": 2.23},
        },
        "disk": {"pct": "59%"},
        "gpu": {"temp_c": 55},
        "agents": {"online": 13, "total": 14},
        "ha": {"connected": True},
        "ollama": {"status": "online"},
        "cloudflare": {"tunnels": "running"},
    }
    result = evaluate_all(fake)
    print(json.dumps(result, indent=2))
