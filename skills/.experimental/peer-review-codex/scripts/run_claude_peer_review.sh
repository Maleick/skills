#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run_claude_peer_review.sh --prompt-file PATH [--workspace PATH] [--model MODEL] [--timeout-seconds N]
EOF
}

PROMPT_FILE=""
WORKSPACE_DIR="$PWD"
MODEL="${PEER_REVIEW_CLAUDE_MODEL:-sonnet}"
CLAUDE_BIN="${PEER_REVIEW_CLAUDE_CLI:-/opt/homebrew/bin/claude}"
TIMEOUT_SECONDS="${PEER_REVIEW_TIMEOUT_SECONDS:-120}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file)
      PROMPT_FILE="${2:-}"
      shift 2
      ;;
    --workspace)
      WORKSPACE_DIR="${2:-}"
      shift 2
      ;;
    --model)
      MODEL="${2:-}"
      shift 2
      ;;
    --timeout-seconds)
      TIMEOUT_SECONDS="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

[[ -n "$PROMPT_FILE" ]] || { echo "PREFLIGHT_FAIL: --prompt-file is required" >&2; exit 1; }
[[ -f "$PROMPT_FILE" ]] || { echo "PREFLIGHT_FAIL: prompt file not found: $PROMPT_FILE" >&2; exit 1; }
[[ -d "$WORKSPACE_DIR" ]] || { echo "PREFLIGHT_FAIL: workspace directory not found: $WORKSPACE_DIR" >&2; exit 1; }
[[ -x "$CLAUDE_BIN" ]] || { echo "PREFLIGHT_FAIL: claude CLI not found at $CLAUDE_BIN" >&2; exit 127; }

PROMPT_CONTENT="$(cat "$PROMPT_FILE")"
CMD=(
  "$CLAUDE_BIN"
  -p
  --output-format text
  --no-session-persistence
  --disable-slash-commands
  --tools ""
  --add-dir "$WORKSPACE_DIR"
)

if [[ -n "$MODEL" ]]; then
  CMD+=(--model "$MODEL")
fi

CMD+=("$PROMPT_CONTENT")
exec python3 - "$TIMEOUT_SECONDS" "${CMD[@]}" <<'PY'
import subprocess
import sys

timeout = int(sys.argv[1])
cmd = sys.argv[2:]

try:
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
except subprocess.TimeoutExpired:
    sys.stderr.write(f"TIMEOUT: claude CLI exceeded {timeout}s\n")
    sys.exit(124)

sys.stdout.write(proc.stdout)
if proc.returncode != 0 and proc.stderr:
    sys.stderr.write(proc.stderr)
sys.exit(proc.returncode)
PY
