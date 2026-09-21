#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Starting Sparta SCADA infrastructure..."
docker compose up -d

echo ""
echo "Running services:"
docker compose ps
