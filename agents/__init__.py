"""
S25 Lumière — Agents Package
Multi-agent autonomous trading infrastructure.

Agents:
- Commander     : Central orchestrator
- TreasuryEngine: ATOM→AKT auto-recharge
- BalanceSentinel: Multi-chain balance monitor
- ArkonSignal   : Trading signal processor
- RiskGuardian  : Circuit breaker + risk manager
- MexcExecutor  : MEXC order execution
- Watchdog      : System health

Usage:
    from agents.commander import Commander
    from agents.treasury_engine import TreasuryEngine
    from agents.balance_sentinel import BalanceSentinel
"""

from .base import BaseAgent, AgentStatus

__version__ = "1.0.0"
__all__ = ["BaseAgent", "AgentStatus"]
