#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LOG_DIR="$REPO_ROOT/logs/ingestion"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%F).log"

source "$REPO_ROOT/.venv/bin/activate"

{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') weekly ingestion run starting ==="

  echo "--- City ingestion ---"
  python -m scripts.ingest_galway_city
  city_status=$?

  echo "--- Cleanup stale raw files ---"
  python -m scripts.cleanup_stale_raw_files
  cleanup_status=$?

  echo "=== $(date '+%Y-%m-%d %H:%M:%S') weekly ingestion run finished (city=$city_status cleanup=$cleanup_status) ==="
} >> "$LOG_FILE" 2>&1

if [ "$city_status" -ne 0 ] || [ "$cleanup_status" -ne 0 ]; then
  exit 1
fi
exit 0
