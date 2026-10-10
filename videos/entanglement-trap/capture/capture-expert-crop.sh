#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PORT=8765
SERVER_LOG="$(mktemp)"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$REPO_ROOT" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true; rm -f "$SERVER_LOG"' EXIT

for _ in {1..30}; do
  if curl --silent --fail "http://127.0.0.1:$PORT/" >/dev/null; then
    break
  fi
  sleep 0.2
done

CAPTURE="$SCRIPT_DIR/assets/trap-expert.png"
playwright screenshot \
  --viewport-size=1920,1080 \
  --wait-for-timeout=500 \
  "http://127.0.0.1:$PORT/videos/entanglement-trap/capture/render-source-crops.html?shot=expert" \
  "$CAPTURE"
cp "$CAPTURE" "$SCRIPT_DIR/../assets/trap-expert.png"
