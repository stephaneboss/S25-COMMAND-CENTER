# TRINITY/S25 Command Mesh Architecture v1.0
## Livré par TRINITY GPT le 2026-04-22, sous commande de Major via Claude backend-ops

## 0. Principe directeur
- **TRINITY = control plane**
- Le laptop n'est jamais une dépendance structurelle
- Runtime prioritaire: Akash > services cloud/tunnels > Dell-Linux (fallback)

## 1. Topologie logique

```
[ Client voix/texte ]
       |
       v
[ TRINITY API Gateway ]
       |
       v
[ Intent Router ] -----------------------> [ Policy Engine ]
       |                                           |
       |                                           v
       |                                 [ Action Guard / Permissions ]
       |
       +-----------------> [ Mission Manager ] <-------------------+
       |                         |                                 |
       |                         v                                 |
       |                   [ Command Bus ]                          |
       |                         |                                 |
       |  +------------------+------------------+                  |
       |  |                  |                  |                  |
       v  v                  v                  v                  |
     [ System State ]  [ Agent Registry ]  [ Incident Manager ]    |
       |                    |                    |                 |
       |                    v                    v                 |
       |             [ State Store ] <--------- [ Health Supervisor ] 
       |                    |
       +-----------------> [ Signal Registry ] <-----------------+
       |                    |
       +-----------------> [ Intel Feed ] ---> [ COMET / ORACLE / ARKON / MERLIN / KIMI ]
```

## 2. Services (12)

| Service | Rôle principal |
|---|---|
| TRINITY API Gateway | Point d'entrée unique, auth, trace_id, rate limit |
| Intent Router | Intent → action système (query/status/mission/signal/incident/noop) |
| Policy Engine | Garde-fou central, permissions d'action |
| Mission Manager | Lifecycle missions (assign/retry/timeout/fermeture) |
| Command Bus | Transport async événements, idempotent, DLQ |
| Agent Registry | Registre vivant agents (id, capacité, heartbeat, reliability) |
| Health Supervisor | Heartbeat, mesh, tunnel, quotas, latence, dérive consensus |
| Incident Manager | info/warning/critical/severe + recommended_actions |
| Signal Registry | Stockage canonique signaux (source/conf/poids/verdict) |
| Intel Feed | Flux normalisé COMET/ORACLE/autres |
| State Store | Source de vérité — agents/missions/incidents/signaux/system_state |
| Ops Journal | Append-only log ops humain+machine |

## 3. Objets canoniques (5)

### 3.1 agent
```json
{
  "agent_id": "COMET",
  "type": "intel",
  "status": "online",
  "runtime": "akash",
  "endpoint_class": "internal",
  "capabilities": ["market_news", "intel_summary", "event_detection"],
  "priority": "normal",
  "cost_tier": "low",
  "reliability_score": 0.91,
  "last_heartbeat_at": "2026-04-22T01:24:10Z",
  "last_seen_at": "2026-04-22T01:24:10Z",
  "cooldown_until": null,
  "metadata": { "owner": "S25" }
}
```
Status enum: `online | degraded | offline | standby | disabled`

### 3.2 mission
```json
{
  "mission_id": "mis_01HS25ABCXYZ",
  "created_at": "2026-04-22T01:30:00Z",
  "created_by": "TRINITY",
  "target_agent": "COMET",
  "task_type": "market_news",
  "intent": "Surveiller news BTC/US macro",
  "priority": "high",
  "status": "assigned",
  "input": { "symbols": ["BTC/USD"], "filters": ["macro","ETF"] },
  "constraints": { "timeout_sec": 120, "max_retries": 2, "require_ack": true },
  "routing": { "selected_by": "TRINITY", "runtime_preference": "akash",
               "fallback_agents": ["MERLIN", "KIMI"] },
  "result": null,
  "error": null,
  "updated_at": "2026-04-22T01:30:03Z"
}
```
Task_type enum: `trading_analysis | market_news | code_generation | strategy_planning | infra_monitoring | fallback`
Priority enum: `low | normal | high | critical`

### 3.3 signal
```json
{
  "signal_id": "sig_01HS25DEFUVW",
  "ts": "2026-04-22T01:31:00Z",
  "source_agent": "ARKON",
  "symbol": "BTC/USD",
  "action": "SELL",
  "confidence": 0.63,
  "weight": 0.75,
  "weighted_confidence": 0.4725,
  "consensus": true,
  "consensus_bonus": 0.15,
  "effective_confidence": 0.6225,
  "verdict": "SIMULATE_EXECUTE",
  "reason": "Auto-relay mesh",
  "context": { "interval": "mesh", "strategy": "auto-relay", "origin": "ARKON5" },
  "linked_incident_id": null
}
```
Action enum: `BUY | SELL | HOLD | ALERT | NO_ACTION`
Verdict enum: `IGNORE | WATCH | SIMULATE_EXECUTE | REVIEW_REQUIRED | BLOCKED_BY_POLICY`

### 3.4 incident
```json
{
  "incident_id": "inc_01HS25GHIJKL",
  "opened_at": "2026-04-22T01:24:15Z",
  "severity": "critical",
  "status": "open",
  "source": "HealthSupervisor",
  "category": "mesh_degradation",
  "title": "Moins de 12 agents online",
  "summary": "Dégradation répétée",
  "evidence": { "mesh_status": "degraded", "tunnel_active": true },
  "impact": { "routing_risk": "high", "execution_risk": "medium" },
  "recommended_actions": ["reroute_to_akash", "disable_noncritical_dispatch"],
  "owner": "TRINITY",
  "resolved_at": null
}
```
Severity enum: `info | warning | critical | severe`
Status enum: `open | acknowledged | mitigating | resolved | closed`

### 3.5 system_state
```json
{
  "ts": "2026-04-22T01:24:15Z",
  "global_status": "critical",
  "pipeline_status": "T3_CRITIQUE_ROUGE",
  "mesh_status": "degraded",
  "tunnel_active": true,
  "agents_online": 3,
  "agents_expected": 14,
  "active_incidents": 2,
  "router_quota_state": "ok",
  "last_signal_at": "2026-04-21T14:42:14Z",
  "control_plane_runtime": "akash",
  "local_dependency": "minimal",
  "notes": ["fallback cloud actif", "surveillance renforcée"]
}
```

## 4. Événements (topics bus)

| Topic | Schema clé |
|---|---|
| `s25.intent.ingest` | event_id, request_id, sender, channel, intent, context, priority |
| `s25.mission.command` | mission_id, command (create/assign/start/cancel/retry/expire/complete/fail), target_agent, payload |
| `s25.mission.status` | mission_id, agent_id, status, progress, message |
| `s25.agent.health` | agent_id, status, latency_ms, error_rate, runtime |
| `s25.signal.ingest` | signal envelope |
| `s25.incident.open` | incident_id, severity, category, owner |
| `s25.incident.resolve` | incident_id, action (acknowledge/mitigate/resolve/close), actor |
| `s25.system.state` | snapshot |

## 5. Routes logiques (6)

### 5.1 POST /ingest_intent — entrée canonique
- Body: `{sender, channel, intent, context, priority}`
- Response: `{request_id, accepted, routed_to, ts}`

### 5.2 POST /route_intent — classification + décision
- Body: `{request_id, intent, context}`
- Response: `{request_id, route, action, policy_result}`

### 5.3 POST /create_mission
- Body: `{created_by, target_agent, task_type, intent, priority, input}`
- Response: `{mission_id, status, target_agent}`

### 5.4 POST /report_health
- Body: `{agent_id, status, latency_ms, runtime}`
- Response: `{accepted, agent_status, next_probe_sec}`

### 5.5 POST /commit_signal
- Body: `{source_agent, symbol, action, confidence, context}`
- Response: `{signal_id, verdict, policy_result}`

### 5.6 POST /resolve_incident
- Body: `{incident_id, action, actor, note}`
- Response: `{incident_id, status}`

## 6. Règles de décision

### 6.1 Routage agent (ordre de préférence)
1. Agent online sur Akash
2. Agent online sur cloud stable
3. Agent degraded si tâche non critique
4. Local Dell-Linux seulement si aucun runtime persistant

### 6.2 Fallback mission
Si target_agent n'ack pas en `timeout_sec` OU status != online OU cooldown actif:
- MissionManager status=blocked
- Tente fallback_agents[0]
- Journalise
- Ouvre incident si priority=critical

### 6.3 Politique signal
- `confidence < 0.45` → IGNORE
- `0.45 ≤ conf < 0.60` → WATCH
- `conf ≥ 0.60` sans blocage policy → SIMULATE_EXECUTE
- Conflit avec incident critique → REVIEW_REQUIRED
- Source non fiable / système severe → BLOCKED_BY_POLICY

### 6.4 Politique incident (ouvrir critical)
- `agents_online < 0.70 × agents_expected`
- pipeline_status contient "CRITIQUE"
- tunnel_active=false SANS fallback cloud
- 3 échecs mission critiques en 10 min
- Quota routeur saturé sans modèle de secours

## 7. Machines d'état

**Agent:** `standby → online → degraded → offline` (+disabled/cooldown)

**Mission:** `draft → queued → assigned → accepted → running → completed` (+failed/expired/blocked/cancelled)

**Incident:** `open → acknowledged → mitigating → resolved → closed` (reopen possible)

## 8. Stockage (tables minimales)

- `agents` — agent_id PK, status, runtime, capabilities, last_heartbeat_at, reliability_score, metadata
- `missions` — mission_id PK, created_by, target_agent, task_type, priority, status, input, constraints, result, error, timestamps
- `signals` — signal_id PK, source_agent, symbol, action, confidence, effective_confidence, verdict, context, ts
- `incidents` — incident_id PK, severity, category, status, source, title, summary, evidence, recommended_actions, opened_at, resolved_at
- `system_state` — snapshot timeline
- `ops_journal` — journal_id, ts, actor, entity_type, entity_id, action, payload (append-only)

## 9. Déploiement (SDL Akash)
```
trinity-api-gateway
intent-router
policy-engine
mission-manager
health-supervisor
incident-manager
signal-registry
state-store
ops-journal
command-bus
```

## 10. SLO opérationnels

- Heartbeat agent: **toutes les 30s**
- Degraded: après **2** heartbeats manqués
- Offline: après **4** heartbeats manqués
- Mission high: ack sous **15s**
- Mission critical: ack sous **5s**
- Health snapshot: toutes les **60s**
- Ops journal: **append-only**

## 11. Convention naming
IDs: `req_* evt_* mis_* sig_* inc_*`
Services: `trinity-* s25-*`
Topics: `s25.intent.ingest`, `s25.mission.command`, `s25.mission.status`, `s25.agent.health`, `s25.signal.ingest`, `s25.incident.open`, `s25.incident.resolve`, `s25.system.state`

## 12. Flux canoniques

**Cas "Lancer COMET":**
Client → POST /ingest_intent → Intent Router → Policy Engine → POST /create_mission → Mission Manager → Command Bus (mission.command) → COMET → Command Bus (mission.status) → State Store → TRINITY réponse

**Cas "mesh dégradé":**
Agent health events → Health Supervisor → Incident Manager → incident.open → system.state update → reroutage Akash

**Cas "signal trading":**
ARKON → /commit_signal → Signal Registry → Policy Engine → verdict → Incident check → ops_journal

## 13. Verrou architecture cible
**Vit sur Akash:** commandement, mémoire, missions, incidents, état système, supervision
**Doit migrer hors laptop:** contrôle dépendant session locale, exécution critique non persistante
**Peut rester local:** dev tools, debug, tests, relais d'urgence non critique

## 14. MVP Order of Build (priorité)
1. TRINITY API Gateway
2. State Store
3. Agent Registry
4. Mission Manager
5. Health Supervisor
6. Incident Manager
7. Policy Engine
8. Signal Registry
9. Ops Journal
10. Command Bus

## 15. Contrat minimal de réussite
L'architecture est valide SI:
- ✅ TRINITY opérant laptop fermé
- ✅ Agent offline ne casse pas le commandement
- ✅ Mission critique reroute automatiquement
- ✅ Incident critique met à jour system_state
- ✅ Tous événements traçables
- ✅ Tout passe par plan de contrôle unique
