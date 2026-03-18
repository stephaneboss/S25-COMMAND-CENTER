# Daily S25 Lumière Pipeline Check

**Agent**: OpenHands (CodeActAgent) on AlienStef — http://10.0.0.97:3001
**Model**: qwen2.5-coder:14b (Ollama local, RTX 3060)
**Schedule**: Daily, any time
**Repo path**: `agents/`

---

## Task Description

Review S25 Lumière agent Python files for quality, fix simple issues, and report findings.

### Steps

1. **Syntax check — all Python agents**
   ```bash
   cd agents/
   python -m py_compile agent_loop.py arkon_signal.py comet_bridge.py \
     kimi_web3_trader.py merlin_feedback_loop.py ninja_routes.py \
     oracle_agent.py onchain_guardian.py risk_guardian.py treasury_engine.py
   echo "Syntax OK"
   ```

2. **Import chain audit**
   - Verify all `from agents.xxx import` or relative imports resolve correctly
   - Flag any `ImportError` patterns that would crash at runtime
   - Check `__init__.py` exports

3. **TODO hunting**
   - Search for `# TODO:` comments in all `.py` files
   - For each TODO that is simple (< 20 lines of code to implement):
     - Implement it
     - Remove the TODO comment
     - Add a brief comment explaining what was done
   - For complex TODOs: just report them

4. **Basic lint with flake8 or ruff** (if available)
   ```bash
   python -m ruff check agents/ --select=E,W,F --ignore=E501 2>/dev/null || \
   python -m flake8 agents/ --max-line-length=120 --ignore=E501,W503 2>/dev/null || \
   echo "No linter available, skipping"
   ```

5. **Dead code detection**
   - Flag any functions defined but never called within the same file
   - Flag any imports that are never used

6. **Findings report**
   Create `agents/DAILY_REPORT_$(date +%Y-%m-%d).md` with:
   - Syntax errors found and fixed
   - TODOs implemented
   - TODOs deferred (with reason)
   - Lint issues fixed
   - Recommendations

7. **Commit**
   ```bash
   git add agents/
   git commit -m "fix(s25): OpenHands daily pipeline check $(date +%Y-%m-%d)"
   ```

---

## Agents to prioritize

| File | Priority | Notes |
|------|----------|-------|
| `agent_loop.py` | HIGH | Main orchestration loop |
| `comet_bridge.py` | HIGH | Perplexity watchman bridge |
| `risk_guardian.py` | HIGH | Risk management |
| `oracle_agent.py` | MEDIUM | Price feeds |
| `onchain_guardian.py` | MEDIUM | On-chain monitoring |
| `ninja_routes.py` | LOW | Route helpers |
| `treasury_engine.py` | LOW | Vault ops |

---

## Expected outcome

- All Python files pass syntax check
- Simple TODOs implemented
- Lint issues reduced
- Daily report committed
