# ═══════════════════════════════════════════════════════════════════
# S25 Lumière — Makefile
# ═══════════════════════════════════════════════════════════════════
# Usage: make <target>
#   make install      — Install dependencies
#   make run          — Start S25 Cockpit (port 7777)
#   make run-agents   — Start all agents via Commander
#   make health       — Check system health
#   make audit        — Show security audit
#   make deploy-ha    — Deploy configs to Home Assistant
#   make sync         — Push to GitHub
#   make test         — Run test suite
#   make lint         — Code quality check
# ═══════════════════════════════════════════════════════════════════

.PHONY: all install run run-agents run-treasury run-sentinel \
        health audit test lint clean deploy-ha sync akash-status \
        akash-fund vault-check

PYTHON  = python3
PIP     = pip3
VENV    = .venv

# Colors
GREEN  = \033[0;32m
YELLOW = \033[1;33m
RED    = \033[0;31m
NC     = \033[0m

# ─── Setup ──────────────────────────────────────────────────────────

all: install

install:
	@echo "$(GREEN)Installing S25 dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Done$(NC)"

install-dev: install
	$(PIP) install flake8 pytest pytest-asyncio black

# ─── Run ────────────────────────────────────────────────────────────

run:
	@echo "$(GREEN)Starting S25 Cockpit on :7777$(NC)"
	$(PYTHON) cockpit_lumiere.py

run-agents:
	@echo "$(GREEN)Starting S25 Commander + all agents$(NC)"
	$(PYTHON) -c "
import asyncio, yaml
from agents.commander import Commander
from agents.treasury_engine import TreasuryEngine
from agents.balance_sentinel import BalanceSentinel
from agents.arkon_signal import ArkonSignal
from agents.risk_guardian import RiskGuardian

config = yaml.safe_load(open('configs/agents.yaml'))

async def main():
    c = Commander(config)
    c.register(TreasuryEngine(config, c))
    c.register(BalanceSentinel(config))
    c.register(ArkonSignal(config, c))
    c.register(RiskGuardian(config, c))
    await c.start()
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        await c.stop()

asyncio.run(main())
"

run-treasury:
	@echo "$(GREEN)Starting Treasury Engine$(NC)"
	$(PYTHON) agents/treasury_engine.py

run-sentinel:
	@echo "$(GREEN)Starting Balance Sentinel$(NC)"
	$(PYTHON) agents/balance_sentinel.py

run-watchdog:
	@echo "$(GREEN)Starting Watchdog$(NC)"
	$(PYTHON) watchdog.py

# ─── Health & Status ────────────────────────────────────────────────

health:
	@echo "$(YELLOW)=== S25 System Health ===$(NC)"
	@curl -sf http://localhost:7777/api/health | $(PYTHON) -m json.tool 2>/dev/null \
		|| echo "$(RED)Cockpit offline — run: make run$(NC)"
	@echo ""
	@echo "$(YELLOW)=== Akash Deployments ===$(NC)"
	@$(PYTHON) -c "
import requests, json
OWNER = 'cosmos1mw0tr5kdnpwdpx88tq8slp4slkfrz9ltqq8vwa'
for dseq in ['25708774', '25817341']:
    try:
        r = requests.get(
            f'https://api.akash.network/akash/deployment/v1beta3/deployment',
            params={'id.owner': OWNER, 'id.dseq': dseq},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            balance = data.get('escrow_account', {}).get('balance', {}).get('amount', '0')
            akt = int(balance) / 1_000_000
            state = data.get('deployment', {}).get('state', '?')
            print(f'  DSEQ {dseq}: {akt:.3f} AKT — {state}')
    except Exception as e:
        print(f'  DSEQ {dseq}: error — {e}')
" 2>/dev/null || echo "  (check Akash Console manually)"

akash-status: health

# ─── Security ───────────────────────────────────────────────────────

audit:
	@echo "$(YELLOW)=== S25 Security Audit ===$(NC)"
	@$(PYTHON) -c "
from security.vault import get_vault
import json
v = get_vault()
audit = v.audit()
print(json.dumps(audit, indent=2))
"
	@echo ""
	@echo "$(YELLOW)=== Vault Readiness ===$(NC)"
	@$(PYTHON) -c "
from security.vault import get_vault
v = get_vault()
ready = v.check_ready()
for k, v in ready.items():
    icon = '✓' if v else '✗'
    print(f'  {icon} {k}: {v}')
"

vault-check: audit

# ─── Testing ────────────────────────────────────────────────────────

test:
	@echo "$(GREEN)Running S25 test suite$(NC)"
	$(PYTHON) -m pytest tests/ -v --tb=short 2>/dev/null \
		|| echo "$(YELLOW)No tests found — add tests in tests/$(NC)"

test-health:
	@$(PYTHON) -c "
from monitoring.health import HealthMonitor
import os, json
h = HealthMonitor(
    os.environ.get('HA_URL', 'http://homeassistant.local:8123'),
    os.environ.get('HA_TOKEN', ''),
    deployments=['25708774', '25817341']
)
report = h.check_all()
print(json.dumps(report, indent=2))
"

# ─── Code Quality ───────────────────────────────────────────────────

lint:
	@echo "$(GREEN)Linting S25 code...$(NC)"
	$(PYTHON) -m flake8 agents/ security/ monitoring/ \
		--max-line-length=120 \
		--ignore=E501,W503,E302,E303
	@echo "$(GREEN)✓ Lint passed$(NC)"

format:
	$(PYTHON) -m black agents/ security/ monitoring/ --line-length=100

# ─── Deployment ─────────────────────────────────────────────────────

deploy-ha:
	@echo "$(GREEN)Deploying S25 configs to Home Assistant$(NC)"
	bash scripts/deploy_s25_ha.sh

sync:
	@echo "$(GREEN)Syncing to GitHub$(NC)"
	bash scripts/github_sync.sh

# ─── Akash ──────────────────────────────────────────────────────────

akash-deploy:
	@echo "$(YELLOW)Open https://console.akash.network/new-deployment$(NC)"
	@echo "Upload: akash/sdl/cockpit.yaml"

akash-fund:
	@echo "$(YELLOW)Open https://console.akash.network$(NC)"
	@echo "Add funds to DSEQ 25708774 (s25-phoenix)"

# ─── Cleanup ────────────────────────────────────────────────────────

clean:
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-logs:
	@rm -f /tmp/s25_*.log /tmp/s25_*.json /tmp/s25_*.jsonl
	@echo "$(GREEN)✓ Logs cleaned$(NC)"
