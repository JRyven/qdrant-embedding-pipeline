# Production-Style Runbook

This runbook describes a generic deployment flow. Adapt paths and service details outside version control.

## Prepare configuration

1. Copy template files to local deployment-specific files.
2. Provide secrets via environment variables or an external secret manager.
3. Confirm generated outputs are written to ignored runtime directories.

## Run the pipeline

```bash
python -m src.tagging.ingest --root /path/to/reference_docs --out /path/to/runtime/ingest.ndjson
python -m src.tagging.embed --in /path/to/runtime/ingest.ndjson --out /path/to/runtime/embeddings.npz
python -m src.tagging.index_qdrant \
  --emb /path/to/runtime/embeddings.npz \
  --meta /path/to/runtime/embeddings_meta.ndjson \
  --collection sample-tagging-prod \
  --db /path/to/runtime/metadata.sqlite \
  --qdrant-url http://localhost:6333
```

## Validate outputs

- Confirm the NDJSON record count is plausible.
- Confirm the embeddings row count matches metadata row count.
- Confirm the Qdrant collection exists and contains the expected number of points.
- Spot-check retrieval results against known sample documents.

## Recovery

If a run fails, stop the pipeline, preserve logs, restore the last known-good generated outputs, and re-run from the last successful stage after correcting the issue.
