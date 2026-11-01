#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ -f "$DIR/.venv/bin/python" ]; then
    PY="$DIR/.venv/bin/python"
else
    PY="python3"
fi

export HOME="$DIR"

# Clean up any lingering process on port 8000 if needed
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

echo "🏨 Starting Hotel Analytics Suite..."
"$PY" start.py "$@"
