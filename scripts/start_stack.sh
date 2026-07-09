#!/usr/bin/env bash
# Brings up the full local stack for LAN testing: Docker (Postgres), Ollama,
# and the web dashboard bound to 0.0.0.0 so collaborators on the same
# network can reach it without installing anything themselves.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

HOST="0.0.0.0"
PORT="${PORT:-8000}"
LOG_DIR="$REPO_ROOT/logs/stack"
mkdir -p "$LOG_DIR"

# Pick up OLLAMA_BASE_URL from .env if not already set in the shell env.
if [ -z "${OLLAMA_BASE_URL:-}" ] && [ -f "$REPO_ROOT/.env" ]; then
  OLLAMA_BASE_URL="$(grep -E '^OLLAMA_BASE_URL=' "$REPO_ROOT/.env" | tail -1 | cut -d= -f2-)"
fi
OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') starting stack ==="

# --- Docker Desktop + Postgres ---
if ! docker info >/dev/null 2>&1; then
  echo "Docker not running, launching Docker Desktop..."
  open -a Docker
  until docker info >/dev/null 2>&1; do
    sleep 2
  done
fi
echo "Docker is up."

docker compose up -d
echo "Postgres container is up."

# --- Ollama ---
case "$OLLAMA_URL" in
  *localhost*|*127.0.0.1*)
    if ! curl -s -o /dev/null "$OLLAMA_URL"; then
      echo "Ollama not reachable, launching local Ollama app..."
      open -a Ollama
      until curl -s -o /dev/null "$OLLAMA_URL"; do
        sleep 2
      done
    fi
    echo "Ollama is up at $OLLAMA_URL."
    ;;
  *)
    echo "OLLAMA_BASE_URL points at a remote host ($OLLAMA_URL) — not launching local Ollama."
    if curl -s -o /dev/null "$OLLAMA_URL"; then
      echo "Remote Ollama is reachable at $OLLAMA_URL."
    else
      echo "WARNING: remote Ollama at $OLLAMA_URL is not reachable. Chat feature will report the AI assistant as unavailable until it is."
    fi
    ;;
esac

# --- Web dashboard ---
if lsof -ti:"$PORT" >/dev/null 2>&1; then
  echo "Port $PORT already in use, assuming dashboard is already running."
else
  source "$REPO_ROOT/.venv/bin/activate"
  LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "$HOST")"
  nohup uvicorn src.web.main:app --host "$HOST" --port "$PORT" \
    >> "$LOG_DIR/$(date +%F).log" 2>&1 &
  disown
  sleep 2
  echo "Dashboard starting on http://$LAN_IP:$PORT"
fi

echo "=== $(date '+%Y-%m-%d %H:%M:%S') stack ready ==="
