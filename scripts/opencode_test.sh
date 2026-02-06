#!/usr/bin/env bash
set -euo pipefail

HOST_DEFAULT="http://localhost:4096"
REPO_DEFAULT="/Users/Apple/Projects/OCB-test"
AGENT_DEFAULT="sisyphus"

HOST="${OPENCODE_HOST:-$HOST_DEFAULT}"
REPO="${OPENCODE_REPO:-$REPO_DEFAULT}"
AGENT="${OPENCODE_AGENT:-$AGENT_DEFAULT}"
TIMEOUT="${OPENCODE_TIMEOUT:-60}"

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required" >&2
  exit 1
fi

msg() {
  printf '%s\n' "$*"
}

api() {
  local method="$1"; shift
  local path="$1"; shift
  curl -s -X "$method" "$HOST$path" "$@"
}

create_session() {
  local title="$1"
  api POST "/session?directory=$REPO" \
    -H 'Content-Type: application/json' \
    -d "{\"title\":\"$title\"}" | jq -r '.id'
}

send_prompt() {
  local session_id="$1"
  local agent="$2"
  local prompt="$3"
  api POST "/session/$session_id/message?directory=$REPO" \
    -H 'Content-Type: application/json' \
    -d "{\"agent\":\"$agent\",\"parts\":[{\"type\":\"text\",\"text\":\"$prompt\"}]}" >/dev/null
}

last_message() {
  local session_id="$1"
  api GET "/session/$session_id/message?directory=$REPO" | jq '.[-1]'
}

wait_for_assistant() {
  local session_id="$1"
  local max_wait="$2"
  local waited=0
  while [ "$waited" -lt "$max_wait" ]; do
    local role
    role=$(api GET "/session/$session_id/message?directory=$REPO" | jq -r '.[-1].info.role')
    if [ "$role" = "assistant" ]; then
      return 0
    fi
    sleep 1
    waited=$((waited+1))
  done
  return 1
}

patch_tool_completed() {
  local session_id="$1"
  local message_id="$2"
  local part_id="$3"
  local output="$4"

  local now
  now=$(python - <<'PY'
import time
print(time.time()*1000)
PY
  )

  api PATCH "/session/$session_id/message/$message_id/part/$part_id?directory=$REPO" \
    -H 'Content-Type: application/json' \
    -d "{\"id\":\"$part_id\",\"sessionID\":\"$session_id\",\"messageID\":\"$message_id\",\"type\":\"tool\",\"callID\":\"question:auto\",\"tool\":\"question\",\"state\":{\"status\":\"completed\",\"input\":{},\"output\":\"$output\",\"title\":\"User responses\",\"metadata\":{},\"time\":{\"start\":$now,\"end\":$now}}}" >/dev/null
}

msg "OpenCode Host: $HOST"
msg "Repo: $REPO"
msg "Agent: $AGENT"

msg "Listing agents..."
api GET "/agent" | jq -r '.[].name'

msg "Creating session..."
SESSION_ID=$(create_session "layered-architect api test")
msg "Session: $SESSION_ID"

PROMPT="Use the layered-architect skill. Detect whether this repo is a fresh start or existing docs; propose a mapping (suggest-only) without modifying files. Ask any required guided questions before proceeding. Strict validation default."
msg "Sending prompt..."
send_prompt "$SESSION_ID" "$AGENT" "$PROMPT"

msg "Waiting for assistant response..."
if ! wait_for_assistant "$SESSION_ID" "$TIMEOUT"; then
  msg "Timeout waiting for assistant response."
  exit 2
fi

ASSIST=$(last_message "$SESSION_ID")
msg "Assistant response:" 
echo "$ASSIST" | jq '.parts[] | {type, text, tool, state}'

# If a question tool is present, auto-respond to continue flow.
QPART=$(echo "$ASSIST" | jq -r '.parts[] | select(.type=="tool" and .tool=="question") | .id' | head -n 1)
MID=$(echo "$ASSIST" | jq -r '.info.id')
if [ -n "$QPART" ] && [ "$QPART" != "null" ]; then
  msg "Question tool detected. Auto-responding with Strict Validation + Validate Current State."
  patch_tool_completed "$SESSION_ID" "$MID" "$QPART" "Primary Action: Validate Current State\nValidation Mode: Strict Validation"
fi

msg "Sending follow-up to proceed with strict validation (read-only)..."
send_prompt "$SESSION_ID" "$AGENT" "Proceed with strict validation. No file modifications; run read-only checks only and report results."

if ! wait_for_assistant "$SESSION_ID" "$TIMEOUT"; then
  msg "Timeout waiting for validation response."
  exit 3
fi

FINAL=$(last_message "$SESSION_ID")
msg "Validation response:" 
echo "$FINAL" | jq '.parts[] | {type, text, tool, state}'

msg "Done."
