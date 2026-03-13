#!/usr/bin/env python3
# ============================================================
# S25 LUMIÈRE — GOUV4 Smart AI Router v1.0
# Gouvernance multi-agents: GPT / Gemini / Claude / Perplexity
# Maximise les quotas gratuits — Orchestration intelligente
# ============================================================

import json
import logging
from datetime import datetime
from collections import defaultdict

log = logging.getLogger("gouv4")

# ─────────────────────────────────────────────────────
# CONFIG AGENTS (priorité + quotas)
# ─────────────────────────────────────────────────────
AGENTS = {
    "gemini": {
        "name": "Gemini Flash",
        "type": "analysis",
        "priority": 1,          # Plus haute priorité pour ARKON-5
        "quota_daily": 1500,    # Requêtes/jour gratuites
        "quota_minute": 15,
        "cost_per_1k": 0.0,
        "best_for": ["trading", "analysis", "json", "retrieval", "embedding", "memory"],
        "key_env": "GEMINI_API_KEY",
    },
    "perplexity": {
        "name": "Perplexity Online",
        "type": "research",
        "priority": 2,
        "quota_daily": 500,
        "quota_minute": 10,
        "cost_per_1k": 0.0,
        "best_for": ["web_search", "news", "market_data"],
        "key_env": "PERPLEXITY_API_KEY",
    },
    "claude": {
        "name": "Claude Haiku",
        "type": "coding",
        "priority": 3,
        "quota_daily": 200,
        "quota_minute": 5,
        "cost_per_1k": 0.0025,
        "best_for": ["code", "yaml", "automation"],
        "key_env": "ANTHROPIC_API_KEY",
    },
    "gpt": {
        "name": "GPT-4o Mini",
        "type": "planning",
        "priority": 4,
        "quota_daily": 300,
        "quota_minute": 10,
        "cost_per_1k": 0.0015,
        "best_for": ["planning", "governance", "strategy"],
        "key_env": "OPENAI_API_KEY",
    },
    "ollama": {
        "name": "Ollama Local",
        "type": "local",
        "priority": 5,         # Fallback gratuit illimité
        "quota_daily": 99999,
        "quota_minute": 60,
        "cost_per_1k": 0.0,
        "best_for": ["fallback", "test"],
        "key_env": None,
    }
}

# Tâches → meilleur agent
TASK_ROUTING = {
    "trading_analysis":  "gemini",
    "knowledge_retrieval": "gemini",
    "semantic_memory":   "gemini",
    "market_news":       "perplexity",
    "code_generation":   "claude",
    "strategy_planning": "gpt",
    "infra_monitoring":  "perplexity",
    "automation_yaml":   "claude",
    "fallback":          "ollama",
}

# ─────────────────────────────────────────────────────
# QUOTA TRACKER
# ─────────────────────────────────────────────────────
class QuotaTracker:
    def __init__(self):
        self.usage = defaultdict(lambda: {"daily": 0, "minute": 0, "last_reset_day": None, "last_reset_min": None})
        self.state_file = "/tmp/gouv4_quotas.json"
        self.load()

    def load(self):
        try:
            with open(self.state_file) as f:
                data = json.load(f)
                self.usage.update(data)
        except Exception:
            pass

    def save(self):
        try:
            with open(self.state_file, "w") as f:
                json.dump(dict(self.usage), f, indent=2)
        except Exception:
            pass

    def reset_if_needed(self, agent_id):
        now = datetime.utcnow()
        u = self.usage[agent_id]
        # Reset daily
        if u["last_reset_day"] != now.strftime("%Y-%m-%d"):
            u["daily"] = 0
            u["last_reset_day"] = now.strftime("%Y-%m-%d")
        # Reset minute
        if u["last_reset_min"] != now.strftime("%Y-%m-%d %H:%M"):
            u["minute"] = 0
            u["last_reset_min"] = now.strftime("%Y-%m-%d %H:%M")

    def can_use(self, agent_id) -> bool:
        self.reset_if_needed(agent_id)
        agent = AGENTS.get(agent_id, {})
        u = self.usage[agent_id]
        return (u["daily"] < agent.get("quota_daily", 0) and
                u["minute"] < agent.get("quota_minute", 0))

    def record_use(self, agent_id):
        self.reset_if_needed(agent_id)
        self.usage[agent_id]["daily"] += 1
        self.usage[agent_id]["minute"] += 1
        self.save()

    def get_report(self) -> dict:
        report = {}
        for aid, agent in AGENTS.items():
            self.reset_if_needed(aid)
            u = self.usage[aid]
            daily_quota = agent["quota_daily"]
            report[aid] = {
                "name": agent["name"],
                "daily_used": u["daily"],
                "daily_quota": daily_quota,
                "daily_pct": round(u["daily"] / max(daily_quota, 1) * 100, 1),
                "minute_used": u["minute"],
                "can_use": self.can_use(aid),
                "cost_est": round(u["daily"] * agent["cost_per_1k"] / 1000, 4)
            }
        return report


# ─────────────────────────────────────────────────────
# GOUV4 ROUTER
# ─────────────────────────────────────────────────────
class GOUV4Router:
    def __init__(self):
        self.quota = QuotaTracker()

    def route(self, task_type: str) -> str:
        """Choisit le meilleur agent disponible pour la tâche"""
        # Agent préféré pour ce type de tâche
        preferred = TASK_ROUTING.get(task_type, "gemini")

        if self.quota.can_use(preferred):
            log.info(f"GOUV4 → {preferred} (preferred for {task_type})")
            return preferred

        # Chercher alternative par priorité
        available = [
            (aid, AGENTS[aid]["priority"])
            for aid in AGENTS
            if self.quota.can_use(aid)
        ]
        available.sort(key=lambda x: x[1])

        if available:
            chosen = available[0][0]
            log.warning(f"GOUV4 fallback: {preferred} quota épuisé → {chosen}")
            return chosen

        # Dernier recours: ollama local
        log.error("GOUV4: Tous les quotas épuisés! → ollama")
        return "ollama"

    def use(self, agent_id: str):
        """Enregistre une utilisation"""
        self.quota.record_use(agent_id)

    def report(self) -> dict:
        """Rapport quotas"""
        return self.quota.get_report()


# ─────────────────────────────────────────────────────
# USAGE EXAMPLE
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    router = GOUV4Router()

    # Exemple d'utilisation
    print("=== GOUV4 SMART AI ROUTER ===")
    print(f"Tâche: trading_analysis → Agent: {router.route('trading_analysis')}")
    print(f"Tâche: market_news      → Agent: {router.route('market_news')}")
    print(f"Tâche: code_generation  → Agent: {router.route('code_generation')}")
    print(f"Tâche: strategy         → Agent: {router.route('strategy_planning')}")

    print("\n=== RAPPORT QUOTAS ===")
    for aid, data in router.report().items():
        status = "✅" if data["can_use"] else "❌"
        print(f"{status} {data['name']:20} | {data['daily_used']:4}/{data['daily_quota']:5} ({data['daily_pct']:5.1f}%) | Cost: ${data['cost_est']:.4f}")
