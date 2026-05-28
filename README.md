# Qdrant Tagging Pipeline

A lightweight Python pipeline for turning Markdown documents into chunked text records, generating embeddings, indexing vectors in Qdrant, and preserving source metadata in SQLite.

This repository is intended to be a clear, public-friendly reference implementation. It uses generic sample data, deterministic mock embeddings for local validation, and optional integrations for real embedding models and a persistent Qdrant service.

## What this project does

The pipeline is organized around a simple file-oriented workflow:

```text
Markdown files
  -> ingest Markdown into chunked NDJSON records
  -> generate embeddings from each chunk
  -> index embeddings in Qdrant
  -> write source metadata to SQLite
```

It is useful for experiments or small applications that need to:

- split Markdown documents into retrieval-friendly chunks;
- generate deterministic mock embeddings for testing;
- generate real embeddings with `sentence-transformers` when model downloads are acceptable;
- build a Qdrant vector collection;
- keep a lightweight SQLite lookup table for source paths, chunk ids, and text snippets;
- test tagging or propagation workflows against a small document corpus.

## Repository status

This is a compact development example rather than a full production platform. The default path is designed to run locally with mock embeddings and an in-memory Qdrant client. Production-style use should provide explicit runtime paths, external service configuration, and deployment-specific secret handling outside version control.

## Requirements

- Python 3.10+
- `pip`
- Optional: Docker, if you want to run a persistent Qdrant service in a container
- Optional: network/model-download access for `sentence-transformers` models

Python dependencies are listed in `requirements.txt`.

## Installation

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the example environment file if you need local environment variables:

```bash
cp .env.example .env
```

Do not commit populated `.env` files, secrets, private service URLs, or machine-specific paths.

## Quickstart: run the local smoke pipeline

The fastest validation path uses the safe sample Markdown files in `mock-data/`, deterministic mock embeddings, and an in-memory Qdrant client:

```bash
bash scripts/run_smoke_local.sh
```

The smoke script writes generated outputs under `data/smoke/`, which is ignored by Git.

Expected outputs include:

```text
data/smoke/ingest.ndjson
data/smoke/embeddings.npz
data/smoke/embeddings_meta.ndjson
data/smoke/metadata.sqlite
```

## Manual pipeline usage

### 1. Ingest Markdown

```bash
python -m src.tagging.ingest \
  --root mock-data \
  --out data/smoke/ingest.ndjson \
  --chunk-words 200
```

The ingest step scans Markdown files, strips YAML frontmatter from the embedded text body, chunks content, and writes one JSON object per line.

Example NDJSON record:

```json
{
  "id": "doc-0",
  "source_path": "mock-data/sample1.md",
  "chunk_id": 0,
  "text": "Chunk text..."
}
```

### 2. Generate embeddings

Use mock embeddings for fast, deterministic local checks:

```bash
python -m src.tagging.embed \
  --in data/smoke/ingest.ndjson \
  --out data/smoke/embeddings.npz \
  --mock \
  --dim 8
```

Use a real embedding model when `sentence-transformers` is installed and model downloads are acceptable:

```bash
python -m src.tagging.embed \
  --in data/smoke/ingest.ndjson \
  --out data/smoke/embeddings.npz \
  --model all-MiniLM-L6-v2
```

The embedding step writes:

- `embeddings.npz` — compressed NumPy archive containing the embedding matrix;
- `embeddings_meta.ndjson` — metadata records preserved in embedding-row order.

### 3. Index vectors in Qdrant

For an in-memory local check:

```bash
python -m src.tagging.index_qdrant \
  --emb data/smoke/embeddings.npz \
  --meta data/smoke/embeddings_meta.ndjson \
  --collection sample-tagging \
  --db data/smoke/metadata.sqlite \
  --qdrant-location :memory:
```

For a persistent Qdrant service:

```bash
python -m src.tagging.index_qdrant \
  --emb data/smoke/embeddings.npz \
  --meta data/smoke/embeddings_meta.ndjson \
  --collection sample-tagging \
  --db data/smoke/metadata.sqlite \
  --qdrant-url http://localhost:6333
```

The indexing step creates or recreates the requested Qdrant collection and writes a SQLite metadata database with source lookup information.

## Configuration

The base configuration lives at:

```text
config/app.yaml
```

Environment-specific overrides live under:

```text
config/develop/
config/production/
```

The loader merges the base configuration with `config/<environment>/<environment>.yaml` when that file exists.

You can inspect merged configuration with:

```bash
python -m src.tagging.config_loader
```

Configuration templates are intentionally generic. For real deployments, copy templates to local deployment-specific files and keep secrets out of Git.

## Data and generated outputs

Tracked sample data is limited to generic Markdown fixtures under `mock-data/`.

Generated pipeline outputs should be written under ignored runtime directories such as:

```text
data/
runs/
```

Do not commit generated embedding archives, SQLite databases, Qdrant snapshots, private corpora, local workspace files, or machine-specific configuration.

## Project layout

```text
.github/                 CI and contributor guidance
.vscode/                 Generic editor recommendations and tasks
config/                  Base and environment-specific configuration examples
documentation/           Architecture, schema, testing, and publication notes
mock-data/               Safe Markdown fixtures for local runs
scripts/                 Smoke, verification, and experimental tagging scripts
src/tagging/             Pipeline implementation
tests/                   Unit and optional integration tests
```

Key modules:

| Path | Purpose |
| --- | --- |
| `src/tagging/ingest.py` | Discovers Markdown files, strips frontmatter from embedded text, chunks content, and writes NDJSON records. |
| `src/tagging/embed.py` | Converts chunk records into deterministic mock embeddings or `sentence-transformers` embeddings. |
| `src/tagging/index_qdrant.py` | Creates a Qdrant collection and writes SQLite source metadata. |
| `src/tagging/config_loader.py` | Loads and merges base and environment-specific YAML configuration. |
| `src/tagging/sanity.py` | Performs basic validation/reporting on generated NDJSON records. |

## Testing and validation

Run the default validation checks:

```bash
python -m compileall src scripts
pytest -q
```

Run the local smoke pipeline:

```bash
bash scripts/run_smoke_local.sh
```

Some behavior depends on optional external resources:

- real embedding generation may download a `sentence-transformers` model;
- persistent indexing requires a reachable Qdrant service;
- integration tests may be skipped when optional services or dependencies are unavailable.

Use mock embeddings for default CI and quick local verification.

## Production-style usage

For a production-style run, prefer explicit input and output paths:

```bash
python -m src.tagging.ingest \
  --root /path/to/reference_docs \
  --out /path/to/runtime/ingest.ndjson

python -m src.tagging.embed \
  --in /path/to/runtime/ingest.ndjson \
  --out /path/to/runtime/embeddings.npz \
  --model all-MiniLM-L6-v2

python -m src.tagging.index_qdrant \
  --emb /path/to/runtime/embeddings.npz \
  --meta /path/to/runtime/embeddings_meta.ndjson \
  --collection sample-tagging-prod \
  --db /path/to/runtime/metadata.sqlite \
  --qdrant-url http://localhost:6333
```

Before using the pipeline with non-sample data:

1. confirm the source corpus is safe to process;
2. write generated outputs to ignored runtime directories;
3. provide service URLs and secrets through environment variables or deployment tooling;
4. validate record counts, embedding row counts, and Qdrant point counts;
5. spot-check retrieval/tagging behavior against known documents.

## Public-readiness checklist

Before publishing, sharing, or accepting external contributions, verify that the repository does not contain:

- secrets, tokens, credentials, or populated `.env` files;
- private hostnames, usernames, local absolute paths, or internal infrastructure names;
- private corpora, generated embeddings, SQLite databases, or Qdrant snapshots;
- personal notes, local workspace files, or redaction utilities;
- stale roadmap material or private planning documents;
- examples that reference real private projects instead of neutral placeholders.

If sensitive files were ever committed, deleting them from the current tree is not enough. Remove them from Git history with a history-rewrite tool such as `git filter-repo` or BFG, then rotate any exposed secrets.

## Contributing

Suggestions, issues, and code edits are welcome. Pull requests should keep examples generic, avoid private or machine-specific configuration, and include tests or validation notes where practical.

See `CONTRIBUTING.md` for the short contribution statement.

## License

See `LICENSE`.
