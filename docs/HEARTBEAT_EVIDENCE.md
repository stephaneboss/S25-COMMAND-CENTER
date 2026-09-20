# Heartbeat evidence

The cron heartbeat observes log modification times. A fresh error log also
counts as activity: `online` is not proof that an agent completed its work.

Cron reports now publish:

| Field | Meaning |
| --- | --- |
| `metadata.health_basis` | `log_mtime` for cron agents; `http_status` for cockpit |
| `metadata.log_age_ms` | Age of the log, not request latency |
| `metadata.expected_interval_sec` | Expected cron interval |
| `metadata.operational_status` | `unknown` until actual task success is verified |
| `metadata.task_success_verified` | `false` for these activity-only probes |
| `latency_ms` | `null`: not measured by the cron probe |
| `error_rate` | `null`: no success/error sample was collected |

The existing `reliability_score` is retained for compatibility. Its metadata
basis explicitly identifies it as log activity or HTTP availability only.
It must not be presented as measured task reliability. A cockpit HTTP 200 does
not verify Home Assistant, Gemini, or any trading workflow.

Missing/unreadable logs report offline. Future-dated logs report degraded with
unknown age. Existing cron thresholds are unchanged: below 2 intervals online,
2 to below 4 degraded, 4 or more offline. This change does not alter routing,
authorization, trading settings, or the global health policy.

## Verification and rollout

Run `python -m unittest discover -s tests -p test_mesh_heartbeat_evidence.py -v`.
The tests use temporary files and mocked HTTP; they send no real heartbeat.

After normal review and deployment to the machine running the heartbeat cron,
wait for its next scheduled tick and read `/api/mesh/agents`. Verify that cron
agents carry the metadata above, with null latency/error rate. Verify that the
deployed commit matches the reviewed revision. Do not run extra trading jobs
to validate this telemetry change. Revert the commit to roll back.

This is the first telemetry correction. A separate task must add producer-owned
execution receipts (last success, last failure, result reference and freshness),
then make operational summaries and UI consume those receipts. No operational
success should be inferred from these heartbeat fields alone.
