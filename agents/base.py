"""
S25 Lumière — Base Agent
========================
Base class for all S25 autonomous agents.

Every agent in the S25 ecosystem inherits from BaseAgent.
Provides: lifecycle management, error recovery, HA reporting.
"""

import asyncio
import logging
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class AgentStatus(Enum):
    IDLE    = "IDLE"
    ACTIVE  = "ACTIVE"
    PAUSED  = "PAUSED"
    ERROR   = "ERROR"
    STOPPED = "STOPPED"


class BaseAgent(ABC):
    """
    Base class for all S25 autonomous agents.

    Each agent:
    - Has a unique name and version
    - Reports status to Home Assistant
    - Handles signals from Commander
    - Auto-recovers from transient errors
    - Logs everything to structured audit trail
    """

    def __init__(self, name: str, version: str = "1.0.0", config: Dict = None):
        self.name    = name
        self.version = version
        self.config  = config or {}
        self.status  = AgentStatus.IDLE

        self.start_time:  Optional[datetime] = None
        self.error_count: int = 0
        self.last_error:  Optional[str] = None

        self._running = False
        self._task:   Optional[asyncio.Task] = None

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
        )
        self.logger = logging.getLogger(f"s25.{name}")

    # ─── Abstract methods (must override) ───────────────────────────────────

    @abstractmethod
    async def run(self):
        """Main agent loop — implement your logic here."""
        pass

    @abstractmethod
    async def handle_signal(self, signal: Dict[str, Any]):
        """Handle incoming signal from Commander."""
        pass

    # ─── Lifecycle ───────────────────────────────────────────────────────────

    async def start(self):
        """Start the agent — called by Commander."""
        self.status     = AgentStatus.ACTIVE
        self.start_time = datetime.utcnow()
        self._running   = True
        self._task      = asyncio.create_task(self._run_loop())
        self.logger.info(f"[{self.name}] v{self.version} — ACTIVE ✓")

    async def stop(self):
        """Graceful shutdown."""
        self._running = False
        self.status   = AgentStatus.STOPPED
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info(f"[{self.name}] STOPPED")

    async def pause(self):
        """Pause agent execution without stopping."""
        self.status = AgentStatus.PAUSED
        self.logger.info(f"[{self.name}] PAUSED")

    async def resume(self):
        """Resume from paused state."""
        self.status = AgentStatus.ACTIVE
        self.logger.info(f"[{self.name}] RESUMED")

    # ─── Error handling ──────────────────────────────────────────────────────

    async def _run_loop(self):
        """Protected run loop with auto-recovery."""
        consecutive_errors = 0

        while self._running:
            try:
                if self.status == AgentStatus.ACTIVE:
                    await self.run()
                    consecutive_errors = 0  # Reset on success
                else:
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                break

            except Exception as e:
                consecutive_errors += 1
                self.error_count += 1
                self.last_error = str(e)
                self.status = AgentStatus.ERROR

                self.logger.error(
                    f"[{self.name}] Error #{consecutive_errors}: {e}"
                )

                # Circuit breaker: too many consecutive errors
                if consecutive_errors >= self.config.get("max_errors", 3):
                    self.logger.critical(
                        f"[{self.name}] Max errors reached — halting agent"
                    )
                    self._running = False
                    break

                # Exponential backoff before retry
                wait = min(30 * consecutive_errors, 300)
                self.logger.info(f"[{self.name}] Retrying in {wait}s...")
                await asyncio.sleep(wait)
                self.status = AgentStatus.ACTIVE

    # ─── Status & Reporting ──────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Get agent status as dict."""
        uptime = "0"
        if self.start_time:
            delta = datetime.utcnow() - self.start_time
            uptime = str(delta).split(".")[0]  # Clean format

        return {
            "name":       self.name,
            "version":    self.version,
            "status":     self.status.value,
            "uptime":     uptime,
            "errors":     self.error_count,
            "last_error": self.last_error,
        }

    def report_ha(
        self,
        ha_url:     str,
        ha_token:   str,
        state:      str,
        attributes: Dict = None
    ):
        """
        Report agent state to Home Assistant entity.
        Entity: sensor.s25_agent_{name}
        """
        entity_id = f"sensor.s25_agent_{self.name.lower().replace('-', '_')}"
        try:
            requests.post(
                f"{ha_url}/api/states/{entity_id}",
                headers={
                    "Authorization": f"Bearer {ha_token}",
                    "Content-Type":  "application/json"
                },
                json={
                    "state":      state,
                    "attributes": {
                        **(attributes or {}),
                        "agent":          self.name,
                        "version":        self.version,
                        "friendly_name":  f"S25 Agent: {self.name}",
                    }
                },
                timeout=5
            )
        except Exception as e:
            self.logger.warning(f"HA report failed: {e}")
