#!/usr/bin/env bash
set -euo pipefail

# Run a local smoke pipeline using mock embeddings to avoid heavy model deps.
# Usage: ./scripts/run_smoke_local.sh

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
MOCK_DATA="$ROOT_DIR/mock-data"
OUT_DIR="$ROOT_DIR/data/smoke"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

echo "1/3 - Running ingest..."
python3 -m src.tagging.ingest --root "$MOCK_DATA" --out "$OUT_DIR/ingest.ndjson" --chunk-words 200

echo "2/3 - Running mock embed (deterministic)..."
python3 -m src.tagging.embed --in "$OUT_DIR/ingest.ndjson" --out "$OUT_DIR/embeddings.npz" --mock --dim 8

echo "3/3 - Building Qdrant index..."
python3 -m src.tagging.index_qdrant --emb "$OUT_DIR/embeddings.npz" --meta "$OUT_DIR/embeddings_meta.ndjson" --collection "smoke-collection" --db "$OUT_DIR/metadata.sqlite" --qdrant-location ":memory:"

if [ -f "$OUT_DIR/metadata.sqlite" ]; then  # Qdrant doesn't create local files
  echo "Smoke run successful: index and DB created at $OUT_DIR"
else
  echo "Smoke run failed: missing outputs" >&2
  exit 2
fi
