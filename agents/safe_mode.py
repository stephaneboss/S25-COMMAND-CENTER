"""Safe mode (Trinity §17) — single source of truth for degraded_mode.json.

P0 2026-09-29: the flag activated in April (global_status=critical) was never
cleared, because the only clear path was `unlink()` in mesh_watchdog_cron and
readers used `DEGRADED_FLAG.exists()`. Result: mission_worker skipped every
non-critical mission for months while system_state said HEALTHY.

Rules enforced here:
  * The file is never deleted — deactivation writes `active: false`.
  * Readers must honour `active` (a file that exists is not "active").
  * Activation carries a TTL, refreshed while the mesh stays critical
  (`confirmed_at`). A flag nobody re-confirms expires on its own.
  * `reconcile(global_status)` aligns the flag with the recomputed state;
  `unknown` never changes anything.

Every function swallows I/O errors: safe mode must never crash a caller.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PATH = REPO / "memory" / "command_mesh" / "degraded_mode.json"
DEFAULT_TTL_S = int(os.environ.get("S25_SAFE_MODE_TTL_S", str(6 * 3600)))

log = logging.getLogger(__name__)


def _path(path: Optional[Path]) -> Path:
    return Path(path) if path else DEFAULT_PATH


def read(path: Optional[Path] = None) -> Dict[str, Any]:
    p = _path(path)
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        log.warning("safe_mode: unreadable %s: %s", p, e)
        return {}


def _write(data: Dict[str, Any], path: Optional[Path]) -> None:
    p = _path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        os.replace(tmp, p)
    except Exception as e:
        log.warning("safe_mode: write failed %s: %s", p, e)


def is_active(path: Optional[Path] = None, now: Optional[float] = None) -> bool:
    """True only if active=true AND not expired."""
    d = read(path)
    if not d.get("active"):
        return False
    now = time.time() if now is None else now
    ttl = d.get("ttl_s", DEFAULT_TTL_S)
    ref = d.get("confirmed_at") or d.get("activated_at")
    try:
        if ttl and ref and now - float(ref) > float(ttl):
            return False
    except (TypeError, ValueError):
        return False
    return True


def activate(reason: str, path: Optional[Path] = None,
             ttl_s: Optional[int] = None, now: Optional[float] = None) -> None:
    now = time.time() if now is None else now
    d = read(path)
    if is_active(path, now=now):
        d["confirmed_at"] = now          # refresh TTL, keep original activation
        d["reason"] = reason or d.get("reason", "")
    else:
        d = {"active": True, "activated_at": now, "confirmed_at": now,
             "reason": reason or ""}
    d["ttl_s"] = int(ttl_s if ttl_s is not None else DEFAULT_TTL_S)
    _write(d, path)


def deactivate(reason: str = "healthy", path: Optional[Path] = None,
               now: Optional[float] = None) -> None:
    d = read(path)
    if d and not d.get("active") and "deactivated_at" in d:
        return  # already off, avoid churning the file / git snapshots
    now = time.time() if now is None else now
    d.update({"active": False, "deactivated_at": now,
              "deactivated_reason": reason or "healthy"})
    _write(d, path)


def reconcile(global_status: str, path: Optional[Path] = None,
              now: Optional[float] = None) -> bool:
    """Align the flag with global_status. Returns resulting active state."""
    gs = (global_status or "unknown").lower()
    if gs in ("critical", "severe"):   # same set as mesh_watchdog_cron
        activate("global_status=%s" % gs, path=path, now=now)
    elif gs in ("healthy", "degraded", "ok", "online"):
        if read(path).get("active"):
            deactivate("global_status=%s" % gs, path=path, now=now)
    return is_active(path, now=now)
