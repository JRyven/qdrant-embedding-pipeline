# Configuration

`config/app.yaml` is the base configuration file. The `environment` field selects an optional override file at `config/<environment>/<environment>.yaml`.

Example:

```yaml
environment: develop
paths:
  data_dir: data
  ingest_ndjson: data/ingest.ndjson
  embeddings_npz: data/embeddings.npz
  qdrant_collection: sample-tagging
  metadata_db: data/metadata.sqlite
```

Use template files as starting points. Do not commit populated secrets, local-only configuration, private hostnames, or absolute paths that reveal personal infrastructure.
