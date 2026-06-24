#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
# Use the PORT env var set by start.sh (already exported)
PORT=${PORT:-4000}
HOSTNAME=0.0.0.0
npm run dev -- -p $PORT -H $HOSTNAME
