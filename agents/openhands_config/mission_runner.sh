#!/usr/bin/env bash
# mission_runner.sh — Posts a coding task to OpenHands on AlienStef, polls for completion.
# Usage: bash mission_runner.sh [task_description]
# Requires: curl, jq

set -euo pipefail

OPENHANDS_URL="http://10.0.0.97:3001"
LOG_FILE="/tmp/openhands_mission.log"
POLL_INTERVAL=10
MAX_POLLS=60   # 10 minutes max

log() {
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$ts] $*" | tee -a "$LOG_FILE"
}

# ─── 1. Health check ──────────────────────────────────────────────────────────

log "Checking OpenHands at $OPENHANDS_URL ..."

if ! curl -sf --connect-timeout 5 "$OPENHANDS_URL/api/options/models" > /dev/null 2>&1; then
  # Try root endpoint as fallback
  if ! curl -sf --connect-timeout 5 "$OPENHANDS_URL/" > /dev/null 2>&1; then
    log "ERROR: OpenHands is not reachable at $OPENHANDS_URL"
    exit 1
  fi
fi

log "OpenHands is alive."

# ─── 2. Task description ─────────────────────────────────────────────────────

TASK_DESCRIPTION="${1:-Review the smajor-command-center Next.js app in the S25 repo. Find any TypeScript errors, missing imports, or broken components. Fix them and commit the changes with message: fix(smajor): OpenHands auto-fix $(date +%Y-%m-%d)}"

log "Task: $TASK_DESCRIPTION"

# ─── 3. Create a new conversation/task via OpenHands API ─────────────────────

log "Posting task to OpenHands..."

CREATE_RESPONSE=$(curl -sf --connect-timeout 10 \
  -X POST "$OPENHANDS_URL/api/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"initial_user_msg\": $(echo "$TASK_DESCRIPTION" | jq -Rs .),
    \"selected_repository\": null
  }" 2>&1) || {
  log "WARNING: /api/conversations failed, trying legacy /api/tasks endpoint..."
  CREATE_RESPONSE=$(curl -sf --connect-timeout 10 \
    -X POST "$OPENHANDS_URL/api/tasks" \
    -H "Content-Type: application/json" \
    -d "{\"task\": $(echo "$TASK_DESCRIPTION" | jq -Rs .)}" 2>&1) || {
    log "ERROR: Could not create task. OpenHands API may have changed."
    log "Response: $CREATE_RESPONSE"
    exit 1
  }
}

log "Create response: $CREATE_RESPONSE"

# Extract conversation/task ID
TASK_ID=$(echo "$CREATE_RESPONSE" | jq -r '.conversation_id // .task_id // .id // empty' 2>/dev/null || echo "")

if [ -z "$TASK_ID" ]; then
  log "WARNING: Could not extract task ID from response. Task was submitted but cannot poll."
  log "Check OpenHands UI at $OPENHANDS_URL for status."
  exit 0
fi

log "Task created. ID: $TASK_ID"

# ─── 4. Poll for completion ───────────────────────────────────────────────────

log "Polling for completion (max ${MAX_POLLS} checks, ${POLL_INTERVAL}s interval)..."

POLLS=0
while [ $POLLS -lt $MAX_POLLS ]; do
  sleep "$POLL_INTERVAL"
  POLLS=$((POLLS + 1))

  STATUS_RESPONSE=$(curl -sf --connect-timeout 10 \
    "$OPENHANDS_URL/api/conversations/$TASK_ID" 2>/dev/null) || \
  STATUS_RESPONSE=$(curl -sf --connect-timeout 10 \
    "$OPENHANDS_URL/api/tasks/$TASK_ID" 2>/dev/null) || \
  STATUS_RESPONSE="{}"

  TASK_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status // .state // "unknown"' 2>/dev/null || echo "unknown")

  log "Poll $POLLS/$MAX_POLLS — status: $TASK_STATUS"

  case "$TASK_STATUS" in
    "finished"|"completed"|"done"|"success")
      log "Task completed successfully!"
      RESULT=$(echo "$STATUS_RESPONSE" | jq -r '.result // .summary // "No summary available."' 2>/dev/null || echo "Completed.")
      log "Result: $RESULT"
      echo "$RESULT" >> "$LOG_FILE"
      exit 0
      ;;
    "error"|"failed"|"failure")
      log "Task FAILED."
      ERROR=$(echo "$STATUS_RESPONSE" | jq -r '.error // .message // "Unknown error"' 2>/dev/null || echo "Unknown error")
      log "Error: $ERROR"
      exit 1
      ;;
    "running"|"in_progress"|"pending"|"started"|"unknown")
      # Still going, keep polling
      ;;
    *)
      log "Unexpected status: $TASK_STATUS — continuing to poll..."
      ;;
  esac
done

log "TIMEOUT: Task did not complete within $((MAX_POLLS * POLL_INTERVAL))s."
log "Check OpenHands UI at $OPENHANDS_URL for task $TASK_ID"
exit 1
