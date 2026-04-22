# TRINITY Stability Layer v1 — Spec complète
## Livré par TRINITY GPT le 2026-04-22, demande de Claude backend-ops

## But
- Encaisser duplication d'événements
- Survivre au flood
- Retry sans tempête
- Protéger le control plane
- Garder missions critiques vivantes même avec mesh dégradé

## 1. Position dans l'architecture
```
[ API Gateway ] → [ Intent Router ] → STABILITY LAYER:
  1. Event Deduplicator
  2. Backpressure Controller
  3. Retry Orchestrator
  4. Circuit Breaker Manager
  5. Priority Scheduler
  6. Lease / Lock Coordinator
  7. Dead Letter Manager
  8. Replay Controller
→ [ Mission Manager | Signal Registry | Incident Manager ]
→ [ Command Bus ↔ State Store ]
```

## 4. Event envelope canonique
```json
{
  "event_id": "evt_01HS25XYZ",
  "event_type": "mission.command",
  "priority": "critical",
  "ts": "2026-04-22T01:40:00Z",
  "source": "MissionManager",
  "trace_id": "trc_01HS25AAA",
  "request_id": "req_01HS25BBB",
  "entity_type": "mission",
  "entity_id": "mis_01HS25CCC",
  "dedupe_key": "mission.command:mis_01HS25CCC:assign:v1",
  "idempotency_key": "mis_01HS25CCC:assign",
  "attempt": 1,
  "max_attempts": 5,
  "ttl_sec": 300,
  "payload": {},
  "meta": { "runtime_preference": "akash" }
}
```

## 5. Event Deduplicator
- TTL: agent.health=90s, system.state=120s, mission.command=24h, mission.status=24h, incident.open=7d, signal.ingest=6h
- Lock TTL: 30s
- Algo: lock-based, if dedupe_key seen in window AND status in [processing,processed] → DUPLICATE_IGNORED

## 6. Backpressure
- States: normal | elevated | congested | shed
- Thresholds: queue>=100 (elevated), >=500 (congested), >=2000 (shed)
- Action: coalesce agent.health + system.state, throttle normal, never drop critical

## 7. Retry Orchestrator
- Backoff: `delay = min(base × 2^(attempt-1), max) + jitter(0..20%)`
- Per type: mission.command (base=2s, max=60s, max_attempts=5), signal.ingest (base=2s, max=30s, attempts=4), incident.open (base=1s, max=15s, attempts=8), agent.health (base=1s, max=5s, attempts=2)
- Escalation mission critical: primary → same if transient → fallback[0] → fallback[1] → incident critical_dispatch_failure

## 8. Circuit Breaker
- States: closed | open | half_open
- Open conditions: fail_rate>50% over 60s (min 10 req), latency_p95>3×, 3 consecutive timeouts, 429 loop, agent offline
- Cooldown: critical=15s, normal=30s
- Granularity: per agent+task_type (e.g. COMET:market_news)

## 9. Priority Scheduler
- Strict priority: critical > high > normal
- Anti-famine: every 20 critical/high tasks, admit 1 normal if backlog + not in shed
- Concurrency by class

## 10. Lease/Lock
- TTL 20s, renew every 5s
- Compare-and-swap on state machine transitions

## 11. DLQ
- Triggers: schema_invalid, max_attempts_reached, policy_denied_def, ttl_expired, no_target+no_fallback
- Critical in DLQ → open incident

## 14. Policies per event type
- agent.health: coalesce yes, retry=2, drop ok
- system.state: coalesce yes, retry=3, never drop if severity changed
- mission.command: strict dedup, no coalesce, retry=5, fallback mandatory, DLQ critical
- signal.ingest: dedup per source+symbol+action+conf_bucket+time_bucket, retry=4
- incident.open: strict dedup per category+entity+severity+window, retry=8, never drop, replay allowed

## 20. Build order
**Phase 1 (indispensable):** Event Deduplicator, Retry Orchestrator, DLQ, Priority Scheduler
**Phase 2:** Circuit Breaker, Lock Coordinator, Backpressure
**Phase 3:** Replay, Watchdog Stability, audit+dashboards

## 21. MVP technique minimal
- Dedup strict par dedupe_key
- Retries avec backoff+jitter
- DLQ
- Strict priority queues
- Breaker basique par agent
- Coalescing agent.health

## 22. Critères d'acceptation
- Test 1: Même event ×10 → 1 traité, 9 ignorés
- Test 2: COMET KO → breaker open, reroute MERLIN/KIMI, mission continue
- Test 3: Flood 5000 signal.ingest normal en 60s → critical continue, normal throttled
- Test 4: 2 workers même mission → 1 seul gagne
- Test 5: DLQ replay → nouvel event_id, pas de duplication

## 23. Seuils v1 pour mesh dégradé
- critical mission ack: <5s
- high mission ack: <15s
- critical queue oldest max: 10s
- breaker open after: 3 timeouts consécutifs
- dedupe lock TTL: 30s
- mission lock TTL: 20s
- safe mode on: backpressure ≥ congested
- safe mode off: 5 min stable
