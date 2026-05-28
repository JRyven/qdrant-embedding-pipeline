# Architecture

The Qdrant tagging pipeline is a small, file-oriented Python application with three primary stages.

```text
Markdown files
  -> ingest.py
  -> chunked NDJSON
  -> embed.py
  -> embeddings.npz + metadata NDJSON
  -> index_qdrant.py
  -> Qdrant collection + SQLite metadata database
```

## Components

| Component | Purpose |
| --- | --- |
| `src/tagging/ingest.py` | Discovers Markdown files, strips frontmatter from embedded text, chunks body content, and writes NDJSON records. |
| `src/tagging/embed.py` | Converts NDJSON text into embeddings using either deterministic mock vectors or `sentence-transformers`. |
| `src/tagging/index_qdrant.py` | Writes vectors to Qdrant and stores source metadata in SQLite. |
| `src/tagging/config_loader.py` | Merges the base configuration with environment-specific overrides. |
| `scripts/` | Provides smoke-test and experimental tagging commands. |

## Design notes

- The pipeline uses plain files between stages so each step can be inspected independently.
- Mock embeddings allow tests and smoke runs without model downloads.
- Qdrant indexing can target an in-memory local client for lightweight validation or a running Qdrant service for integration testing.
- Sample data is generic and should remain safe to publish.
