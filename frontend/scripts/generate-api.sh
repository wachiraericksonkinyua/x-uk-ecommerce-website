#!/usr/bin/env bash
# Regenerate the OpenAPI schema + TypeScript types from the running backend.
#
#   1. start the backend:  uvicorn app.main:app --reload
#   2. run:                bash frontend/scripts/generate-api.sh
#
# Re-run this whenever the backend routes change so the frontend types stay in sync.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${API_URL:-http://127.0.0.1:8000}"

echo "Fetching $API_URL/openapi.json"
curl -s "$API_URL/openapi.json" -o "$ROOT/openapi.json"

echo "Generating TypeScript types -> packages/api/src/schema.d.ts"
npx --yes openapi-typescript "$ROOT/openapi.json" -o "$ROOT/packages/api/src/schema.d.ts"

echo "Done."
