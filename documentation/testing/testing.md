# Testing

Run the standard checks:

```bash
python -m compileall src scripts
pytest
```

Run a local smoke pipeline with deterministic mock embeddings:

```bash
bash scripts/run_smoke_local.sh
```

Some integration behavior requires optional services, such as a running Qdrant instance or model downloads for `sentence-transformers`. Prefer mock-mode tests for default CI unless an integration test explicitly requires external services.
