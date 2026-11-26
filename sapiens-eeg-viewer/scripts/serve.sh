#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8000}"

printf 'Serving demo at http://127.0.0.1:%s/web/\n' "$PORT"
exec python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$PROJECT_ROOT"
