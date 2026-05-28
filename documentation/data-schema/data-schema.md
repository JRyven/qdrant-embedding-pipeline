# Data Schema

## Ingest NDJSON

Each line emitted by `src.tagging.ingest` is a JSON object:

```json
{
  "id": "doc-0",
  "source_path": "mock-data/sample1.md",
  "chunk_id": 0,
  "text": "Chunk text..."
}
```

## Embeddings archive

`src.tagging.embed` writes a compressed NumPy archive containing an `embeddings` array. The companion metadata file preserves NDJSON records in the same order as the embedding rows.

## SQLite metadata table

`src.tagging.index_qdrant` writes a `documents` table with document id, source path, chunk id, and a short text snippet.
