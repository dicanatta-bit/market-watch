#!/usr/bin/env bash
# VPS-only data refresh. No frontend build, generated files, or Git writes.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/backend"
PYTHON="$ROOT/backend/venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "ERROR: virtualenv Python tidak ditemukan: $PYTHON" >&2
  exit 1
fi
exec 9>"$ROOT/backend/.pipeline.lock"
if ! flock -n 9; then
  echo "ERROR: pipeline lain masih berjalan" >&2
  exit 1
fi
echo "=== Market Watch refresh $(date -Is) ==="
PIPELINE_TRIGGER="${PIPELINE_TRIGGER:-cron}"
exec "$PYTHON" -m app.scrapers.pipeline --trigger "$PIPELINE_TRIGGER"
