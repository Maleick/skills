#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LISTENER_SCRIPT="$SCRIPT_DIR/app_server_compaction_listener.py"

DEFAULT_PROJECT_RAW="$(basename "$PWD")"
DEFAULT_PROJECT="$(printf '%s' "$DEFAULT_PROJECT_RAW" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-*//;s/-*$//')"
DEFAULT_PROJECT="${DEFAULT_PROJECT:-workspace}"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

PROJECT="${AUTO_MEMORY_PROJECT:-$DEFAULT_PROJECT}"
OBJECTIVE="${AUTO_MEMORY_OBJECTIVE:-Continue the active task using preserved context after compaction.}"
LIMIT="${AUTO_MEMORY_LIMIT:-8}"
OUTPUT_FRAMING="${AUTO_MEMORY_OUTPUT_FRAMING:-jsonl}"
REQUEST_ID_PREFIX="${AUTO_MEMORY_REQUEST_ID_PREFIX:-auto-memory}"
PROMPT_OUT="${AUTO_MEMORY_PROMPT_OUT:-$CODEX_HOME/tmp/auto-memory-reinjection.txt}"
JSONL_LOG="${AUTO_MEMORY_LOG:-$CODEX_HOME/tmp/auto-memory-listener.log}"
QUERY="${AUTO_MEMORY_QUERY:-}"
INPUT_FILE="${AUTO_MEMORY_INPUT_FILE:-}"
QUIET="${AUTO_MEMORY_QUIET:-1}"

mkdir -p "$(dirname "$PROMPT_OUT")" "$(dirname "$JSONL_LOG")"

CMD=(
  python3 "$LISTENER_SCRIPT"
  --project "$PROJECT"
  --objective "$OBJECTIVE"
  --limit "$LIMIT"
  --inject-turn-start
  --output-framing "$OUTPUT_FRAMING"
  --request-id-prefix "$REQUEST_ID_PREFIX"
  --prompt-out "$PROMPT_OUT"
  --jsonl-log "$JSONL_LOG"
)

if [[ -n "$QUERY" ]]; then
  CMD+=(--query "$QUERY")
fi

if [[ -n "$INPUT_FILE" ]]; then
  CMD+=(--input-file "$INPUT_FILE")
fi

if [[ "$QUIET" == "1" ]]; then
  CMD+=(--quiet)
fi

CMD+=("$@")

echo "Starting auto-memory listener" >&2
echo "project=$PROJECT" >&2
echo "objective=$OBJECTIVE" >&2
echo "prompt_out=$PROMPT_OUT" >&2
echo "log=$JSONL_LOG" >&2

exec "${CMD[@]}"
