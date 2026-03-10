#!/usr/bin/env python3

import logging
import os
from typing import Any, Dict, Optional

import requests
from security.vault import vault_get


log = logging.getLogger("s25.cockpit_client")


class CockpitClient:
    def __init__(self, base_url: Optional[str] = None, shared_secret: Optional[str] = None, timeout: int = 15):
        self.base_url = (base_url or os.getenv("COCKPIT_URL", "http://localhost:7777")).rstrip("/")
        self.shared_secret = (
            shared_secret
            if shared_secret is not None
            else (vault_get("S25_SHARED_SECRET", os.getenv("S25_SHARED_SECRET", "")) or "")
        )
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.shared_secret:
            headers["X-S25-Secret"] = self.shared_secret
        return headers

    def _get(self, path: str, **params: Any) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                params=params or None,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            log.warning("cockpit GET %s failed: %s", path, exc)
            return None

    def _post(self, path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            response = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            log.warning("cockpit POST %s failed: %s", path, exc)
            return None

    def heartbeat(self, agent: str, note: str = "") -> Optional[Dict[str, Any]]:
        return self._post("/api/memory/ping", {"agent": agent, "note": note})

    def update_state(
        self,
        agent: str,
        updates: Optional[Dict[str, Any]] = None,
        pipeline: Optional[Dict[str, Any]] = None,
        market: Optional[Dict[str, Any]] = None,
        intel: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {"agent": agent}
        if updates:
            payload["updates"] = updates
        if pipeline:
            payload["pipeline"] = pipeline
        if market:
            payload["market"] = market
        if intel:
            payload["intel"] = intel
        return self._post("/api/memory/state", payload)

    def get_missions(self) -> Optional[Dict[str, Any]]:
        return self._get("/api/missions")

    def get_shared_memory(self) -> Optional[Dict[str, Any]]:
        return self._get("/api/memory")

    def get_agents_state(self) -> Optional[Dict[str, Any]]:
        return self._get("/api/memory/state")

    def get_mesh_status(self) -> Optional[Dict[str, Any]]:
        return self._get("/api/mesh/status")

    def get_router_report(self) -> Optional[Dict[str, Any]]:
        return self._get("/api/router/report")

    def route_task(self, task_type: str) -> Optional[Dict[str, Any]]:
        return self._post("/api/router/route", {"task_type": task_type})

    def create_mission(
        self,
        created_by: str,
        target: str,
        task_type: str,
        intent: str,
        priority: str = "normal",
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "created_by": created_by,
            "target": target,
            "task_type": task_type,
            "intent": intent,
            "priority": priority,
        }
        if context is not None:
            payload["context"] = context
        return self._post("/api/missions", payload)

    def update_mission(
        self,
        mission_id: str,
        status: str,
        actor: str,
        result: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "mission_id": mission_id,
            "status": status,
            "actor": actor,
        }
        if result is not None:
            payload["result"] = result
        if context is not None:
            payload["context"] = context
        return self._post("/api/missions/update", payload)

    def get_status(self) -> Optional[Dict[str, Any]]:
        return self._get("/api/status")
