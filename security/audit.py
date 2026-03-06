"""
S25 Lumière — Security Audit Log
==================================
Append-only audit trail for all sensitive operations.

Every trade, swap, API call, and config change gets logged.
Logs are hashed for integrity verification.
Sensitive values are automatically redacted.
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("s25.audit")


class AuditLog:
    """
    Append-only security audit log.

    Format: JSONL (one JSON object per line)
    Location: /tmp/s25_audit.jsonl (or configured path)

    Usage:
        audit = AuditLog()
        audit.log("TRADE_SIGNAL", "arkon_signal", {"symbol": "BTC/USDT"})
        audit.log("SWAP_EXECUTED", "treasury_engine", {...}, risk="HIGH")
    """

    # Event types
    EVENTS = {
        "API_CALL":          "External API call",
        "TRADE_SIGNAL":      "Trading signal received",
        "ORDER_PLACED":      "Exchange order placed",
        "ORDER_CANCELLED":   "Exchange order cancelled",
        "ORDER_FILLED":      "Exchange order filled",
        "SWAP_EXECUTED":     "Cross-chain swap executed",
        "SWAP_FAILED":       "Cross-chain swap failed",
        "KEY_ACCESSED":      "API key accessed",
        "CONFIG_CHANGED":    "System config changed",
        "AGENT_STARTED":     "Agent started",
        "AGENT_STOPPED":     "Agent stopped",
        "AGENT_ERROR":       "Agent encountered error",
        "CIRCUIT_BREAKER":   "Circuit breaker triggered",
        "BALANCE_LOW":       "Balance below threshold",
        "BALANCE_CRITICAL":  "Balance critically low",
        "HA_UPDATE":         "HA entity updated",
        "RISK_BREACH":       "Risk limit breached",
        "MANUAL_OVERRIDE":   "Manual operator override",
    }

    # Risk levels
    RISK_INFO     = "INFO"
    RISK_LOW      = "LOW"
    RISK_MEDIUM   = "MEDIUM"
    RISK_HIGH     = "HIGH"
    RISK_CRITICAL = "CRITICAL"

    # Fields that should never appear in logs
    _SENSITIVE_PATTERNS = {
        "key", "token", "secret", "password", "mnemonic",
        "seed", "private", "auth", "bearer"
    }

    def __init__(self, log_file: str = "/tmp/s25_audit.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._count = 0

    def log(
        self,
        event_type: str,
        agent:      str,
        details:    Dict[str, Any],
        risk:       str = "INFO",
        summary:    str = ""
    ):
        """
        Log an audit event.

        Args:
            event_type: One of EVENTS keys
            agent:      Agent name that generated the event
            details:    Event details (sensitive values auto-redacted)
            risk:       Risk level (INFO/LOW/MEDIUM/HIGH/CRITICAL)
            summary:    Short human-readable description
        """
        self._count += 1

        entry = {
            "n":       self._count,
            "ts":      datetime.utcnow().isoformat() + "Z",
            "event":   event_type,
            "agent":   agent,
            "risk":    risk,
            "summary": summary or details.get("summary", ""),
            "details": self._sanitize(details),
            "hash":    ""
        }

        # Integrity hash (covers all fields except hash itself)
        payload = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                             sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

        # Write to JSONL file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Audit write failed: {e}")

        # Also log to Python logger at appropriate level
        log_msg = f"[AUDIT] {event_type} | {agent} | {entry['summary']}"
        if risk == self.RISK_CRITICAL:
            logger.critical(log_msg)
        elif risk == self.RISK_HIGH:
            logger.error(log_msg)
        elif risk == self.RISK_MEDIUM:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    def _sanitize(self, details: Dict) -> Dict:
        """Redact sensitive values from log entries."""
        result = {}
        for k, v in details.items():
            if any(s in k.lower() for s in self._SENSITIVE_PATTERNS):
                result[k] = "[REDACTED]"
            elif isinstance(v, dict):
                result[k] = self._sanitize(v)
            elif isinstance(v, str) and len(v) > 100:
                # Truncate very long strings
                result[k] = v[:100] + "...[truncated]"
            else:
                result[k] = v
        return result

    def get_recent(self, n: int = 50, risk_filter: Optional[str] = None) -> List[Dict]:
        """Get recent audit entries, optionally filtered by risk level."""
        if not self.log_file.exists():
            return []

        try:
            lines = self.log_file.read_text(encoding="utf-8").strip().split("\n")
            entries = [json.loads(l) for l in lines if l.strip()]

            if risk_filter:
                entries = [e for e in entries if e.get("risk") == risk_filter]

            return entries[-n:]
        except Exception as e:
            logger.error(f"Audit read error: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get audit statistics."""
        entries = self.get_recent(10000)
        if not entries:
            return {"total": 0}

        risk_counts = {}
        event_counts = {}

        for e in entries:
            risk_counts[e.get("risk", "?")] = risk_counts.get(e.get("risk", "?"), 0) + 1
            event_counts[e.get("event", "?")] = event_counts.get(e.get("event", "?"), 0) + 1

        return {
            "total":        len(entries),
            "by_risk":      risk_counts,
            "by_event":     event_counts,
            "first_entry":  entries[0].get("ts") if entries else None,
            "last_entry":   entries[-1].get("ts") if entries else None,
        }

    def verify_integrity(self, n: int = 100) -> Dict:
        """Verify hash integrity of recent entries."""
        entries = self.get_recent(n)
        valid = 0
        invalid = []

        for entry in entries:
            stored_hash = entry.get("hash", "")
            payload = json.dumps(
                {k: v for k, v in entry.items() if k != "hash"},
                sort_keys=True, separators=(",", ":")
            )
            expected = hashlib.sha256(payload.encode()).hexdigest()[:16]

            if stored_hash == expected:
                valid += 1
            else:
                invalid.append(entry.get("n"))

        return {
            "checked":      len(entries),
            "valid":        valid,
            "tampered":     len(invalid),
            "tampered_ids": invalid
        }


# ─── Singleton ───────────────────────────────────────────────────────────────

_audit: Optional[AuditLog] = None


def get_audit(log_file: str = "/tmp/s25_audit.jsonl") -> AuditLog:
    """Get or create the global audit log instance."""
    global _audit
    if _audit is None:
        _audit = AuditLog(log_file)
    return _audit


def audit(event: str, agent: str, details: Dict, risk: str = "INFO", summary: str = ""):
    """Shorthand: log to global audit."""
    get_audit().log(event, agent, details, risk, summary)
