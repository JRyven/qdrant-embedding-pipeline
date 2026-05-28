#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./scripts/run_production_sample.sh --root /path/to/corpus/original --out-base runs/run-20260112 --dry-run

ROOT=""
OUT_BASE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --root) ROOT="$2"; shift 2;;
    --out-base) OUT_BASE="$2"; shift 2;;
    --dry-run) DRY_RUN=true; shift;;
    --help) echo "Usage: $0 --root /path/to/corpus --out-base /path/to/out --dry-run"; exit 0;;
    *) echo "Unknown arg $1"; exit 1;;
  esac
done

if [[ -z "$ROOT" ]]; then
  echo "Error: --root is required" >&2
  exit 2
fi

if [[ -z "$OUT_BASE" ]]; then
  NOW=$(date +%y%m%d)
  OUT_BASE="runs/run-$NOW"
fi

echo "Root corpus: $ROOT"
echo "Output base: $OUT_BASE"
echo "Dry run: $DRY_RUN"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry run: no changes will be written."
fi

# Create safe, dated run dir by copying the source corpus (rsync preserves structure)
RUN_DIR="${OUT_BASE}"
if [[ "$DRY_RUN" == "false" ]]; then
  mkdir -p "$RUN_DIR"
  echo "Copying files to $RUN_DIR ..."
  rsync -av --exclude '*/.git*' "$ROOT"/ "$RUN_DIR"/
else
  echo "Skipping copy in dry-run mode."
fi

# Paths for pipeline outputs inside the run dir
DATA_DIR="${RUN_DIR}/data"
INGEST_NDJSON="${DATA_DIR}/ingest.ndjson"
EMB_NPZ="${DATA_DIR}/embeddings.npz"
INDEX_COLLECTION="sample-tagging"
META_DB="${DATA_DIR}/metadata.sqlite"

if [[ "$DRY_RUN" == "false" ]]; then
  mkdir -p "$DATA_DIR"
fi

echo "Running ingest..."
if [[ "$DRY_RUN" == "false" ]]; then
  python3 -m src.tagging.ingest --root "$RUN_DIR" --out "$INGEST_NDJSON"
else
  echo "Dry-run: python -m src.tagging.ingest --root $RUN_DIR --out $INGEST_NDJSON"
fi

echo "Sanity checking NDJSON for PII and structure..."
if [[ "$DRY_RUN" == "false" ]]; then
  python3 -m src.tagging.sanity --ndjson "$INGEST_NDJSON" --report "${DATA_DIR}/sanity_report.json"
else
  echo "Dry-run: python -m src.tagging.sanity --ndjson $INGEST_NDJSON --report ${DATA_DIR}/sanity_report.json"
fi

echo "Running embed..."
if [[ "$DRY_RUN" == "false" ]]; then
  python3 -m src.tagging.embed --in "$INGEST_NDJSON" --out "$EMB_NPZ"
else
  echo "Dry-run: python -m src.tagging.embed --in $INGEST_NDJSON --out $EMB_NPZ"
fi

echo "Building Qdrant index..."
if [[ "$DRY_RUN" == "false" ]]; then
  python3 -m src.tagging.index_qdrant --emb "$EMB_NPZ" --meta "$INGEST_NDJSON" --collection "$INDEX_COLLECTION" --db "$META_DB"
else
  echo "Dry-run: python -m src.tagging.index_qdrant --emb $EMB_NPZ --meta $INGEST_NDJSON --collection $INDEX_COLLECTION --db $META_DB"
fi

echo "Run completed. Outputs (when not dry-run) are under: $RUN_DIR"
echo "Sanity report: ${DATA_DIR}/sanity_report.json"

exit 0
