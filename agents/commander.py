"""
S25 Lumière — Commander
=======================
Central orchestrator for all S25 autonomous agents.

The Commander is Mission Control:
- Registers and manages agent lifecycle
- Routes signals (ARKON, market data, system events)
- Enforces circuit breakers for risk management
- Reports system health to Home Assistant

Usage:
    from agents.commander import Commander
    from agents.treasury_engine import TreasuryEngine
    from agents.balance_sentinel import BalanceSentinel

    commander = Commander(config)
    commander.register(TreasuryEngine(config))
    commander.register(BalanceSentinel(config))
    await commander.start()
"""

import asyncio
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from .base import BaseAgent, AgentStatus

logger = logging.getLogger("s25.commander")


class Commander:
    """
    S25 Commander — Multi-Agent Mission Control.

    Signal Types:
    - ARKON_SIGNAL    : Trading signal from ARKON-5 model
    - MARKET_DATA     : Price/volume update
    - BALANCE_ALERT   : Low balance warning
    - SYSTEM_EVENT    : Infrastructure event (deployment, restart)
    - RISK_BREACH     : Risk limit exceeded
    - MANUAL          : Manual override from operator

    Routing:
    - target="all"           → All active agents
    - target="agent_name"    → Specific agent
    - target=["a", "b"]      → List of agents
    """

    VERSION = "1.0.0"

    def __init__(self, config: Dict = None):
        self.config     = config or {}
        self.agents:    Dict[str, BaseAgent] = {}
        self.running    = False
        self.start_time: Optional[datetime] = None

        self._signal_queue    = asyncio.Queue(maxsize=1000)
        self._circuit_breaker = False
        self._processed       = 0
        self._dropped         = 0

        # HA reporting config
        self._ha_url   = self.config.get("ha_url", "")
        self._ha_token = self.config.get("ha_token", "")

    # ─── Agent Registry ──────────────────────────────────────────────────────

    def register(self, agent: BaseAgent) -> "Commander":
        """Register an agent. Returns self for chaining."""
        self.agents[agent.name] = agent
        logger.info(f"Registered: {agent.name} v{agent.version}")
        return self

    def unregister(self, name: str):
        """Remove agent from registry."""
        self.agents.pop(name, None)
        logger.info(f"Unregistered: {name}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return self.agents.get(name)

    # ─── Signal Routing ──────────────────────────────────────────────────────

    async def dispatch(self, signal: Dict[str, Any]):
        """
        Queue a signal for routing.

        Signal format:
        {
            "type":   "ARKON_SIGNAL",       # Required
            "target": "all",                # Optional (default: "all")
            "data":   {...},                # Payload
            "source": "kimi_proxy",         # Who sent this
            "ts":     "2026-03-06T...",     # Timestamp
        }
        """
        if self._circuit_breaker:
            self._dropped += 1
            logger.warning(
                f"Circuit breaker OPEN — signal dropped: "
                f"{signal.get('type')} (total dropped: {self._dropped})"
            )
            return

        signal.setdefault("ts", datetime.utcnow().isoformat())
        try:
            self._signal_queue.put_nowait(signal)
        except asyncio.QueueFull:
            logger.error(f"Signal queue full — dropping: {signal.get('type')}")

    async def _process_signals(self):
        """Main signal processing loop."""
        while self.running:
            try:
                signal = await asyncio.wait_for(
                    self._signal_queue.get(), timeout=1.0
                )
                await self._route_signal(signal)
                self._processed += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Signal processing error: {e}")

    async def _route_signal(self, signal: Dict[str, Any]):
        """Route signal to target agents."""
        signal_type = signal.get("type", "unknown")
        target      = signal.get("target", "all")

        # Resolve targets
        if target == "all":
            targets = list(self.agents.values())
        elif isinstance(target, list):
            targets = [self.agents[n] for n in target if n in self.agents]
        elif isinstance(target, str) and target in self.agents:
            targets = [self.agents[target]]
        else:
            logger.warning(f"Unknown target: {target} for signal: {signal_type}")
            return

        logger.debug(
            f"Routing {signal_type} → "
            f"{[a.name for a in targets if a.status == AgentStatus.ACTIVE]}"
        )

        # Dispatch to each active agent
        for agent in targets:
            if agent.status == AgentStatus.ACTIVE:
                try:
                    await agent.handle_signal(signal)
                except Exception as e:
                    logger.error(
                        f"Agent {agent.name} failed on {signal_type}: {e}"
                    )

    # ─── Circuit Breaker ─────────────────────────────────────────────────────

    def trigger_circuit_breaker(self, reason: str = ""):
        """Emergency halt — stop all signal routing."""
        self._circuit_breaker = True
        msg = f"CIRCUIT BREAKER TRIGGERED — {reason or 'emergency halt'}"
        logger.critical(msg)
        self._notify_ha("CIRCUIT_BREAKER", msg)

    def reset_circuit_breaker(self):
        """Resume normal operations after investigation."""
        self._circuit_breaker = False
        logger.info("Circuit breaker RESET — Operations resumed")
        self._notify_ha("CIRCUIT_BREAKER_RESET", "Normal operations resumed")

    # ─── Lifecycle ───────────────────────────────────────────────────────────

    async def start(self):
        """Start Commander and all registered agents."""
        self.running    = True
        self.start_time = datetime.utcnow()

        logger.info(f"═══ S25 Commander v{self.VERSION} BOOTING ═══")
        logger.info(f"Starting {len(self.agents)} agents...")

        failed = []
        for name, agent in self.agents.items():
            # Check if agent is enabled in config
            agent_config = self.config.get("agents", {}).get(name, {})
            if not agent_config.get("enabled", True):
                logger.info(f"  ⊘ {name} (disabled in config)")
                continue

            try:
                await agent.start()
                logger.info(f"  ✓ {name}")
            except Exception as e:
                logger.error(f"  ✗ {name}: {e}")
                failed.append(name)

        # Start signal processor
        asyncio.create_task(self._process_signals())

        active = len(self.agents) - len(failed)
        logger.info(f"═══ {active}/{len(self.agents)} agents ONLINE ═══")

        if failed:
            logger.warning(f"Failed to start: {failed}")

        self._notify_ha(
            "COMMANDER_START",
            f"Commander online — {active} agents active"
        )

    async def stop(self):
        """Graceful shutdown of all agents."""
        logger.info("Commander shutdown initiated...")
        self.running = False

        for name, agent in self.agents.items():
            try:
                await agent.stop()
                logger.info(f"  ✓ stopped {name}")
            except Exception as e:
                logger.error(f"  ✗ error stopping {name}: {e}")

        self._notify_ha("COMMANDER_STOP", "Commander shutdown complete")
        logger.info("Commander shutdown complete")

    # ─── Status ──────────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Full system status snapshot."""
        return {
            "commander":         "ACTIVE" if self.running else "STOPPED",
            "version":           self.VERSION,
            "uptime":            self._get_uptime(),
            "circuit_breaker":   self._circuit_breaker,
            "signals_processed": self._processed,
            "signals_dropped":   self._dropped,
            "queue_size":        self._signal_queue.qsize(),
            "agents": {
                name: agent.get_status()
                for name, agent in self.agents.items()
            }
        }

    def _get_uptime(self) -> str:
        if not self.start_time:
            return "0"
        delta = datetime.utcnow() - self.start_time
        return str(delta).split(".")[0]

    # ─── HA Integration ──────────────────────────────────────────────────────

    def _notify_ha(self, event: str, message: str):
        """Send commander event to Home Assistant."""
        if not self._ha_url or not self._ha_token:
            return
        try:
            requests.post(
                f"{self._ha_url}/api/states/sensor.s25_commander",
                headers={
                    "Authorization": f"Bearer {self._ha_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "state": "ACTIVE" if self.running else "STOPPED",
                    "attributes": {
                        "event":             event,
                        "message":           message,
                        "agents_active":     sum(
                            1 for a in self.agents.values()
                            if a.status == AgentStatus.ACTIVE
                        ),
                        "circuit_breaker":   self._circuit_breaker,
                        "friendly_name":     "S25 Commander"
                    }
                },
                timeout=5
            )
        except Exception:
            pass  # Don't crash commander if HA is down
