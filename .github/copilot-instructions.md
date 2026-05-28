# Copilot & AI Agent Instructions for Write Tagging

## Project Overview
- **Write Tagging** is a minimal ML pipeline for tagging and embedding markdown documents.
- The architecture is modular, with clear separation between ingestion, embedding, indexing, and configuration.
- Documentation is highly structured and lives under `documentation/` with topic-based subfolders and index files.

## Key Workflows
- **Ingest, Embed, Index:**
  - `python -m src.tagging.ingest --root /path/to/corpus --out data/ingest.ndjson`
  - `python -m src.tagging.embed --in data/ingest.ndjson --out data/embeddings.npz`
  - `python -m src.tagging.index_qdrant --emb data/embeddings.npz --meta data/ingest_meta.ndjson --collection tagging-collection --db data/metadata.sqlite`
- **Configuration:**
  - Canonical config: `config/app.yaml` (merged with `config/<environment>/<environment>.yaml`)
  - Use `python -m src.tagging.config_loader` for deterministic config merging.
- **Testing:**
  - Run all tests: `npm test` (see `tests/` for Python and JS tests)
  - Lint: `npm run lint`
  - Build: `npm run build`

## Architecture & Patterns
- **Pipeline:** Ingestion → Embedding → Indexing, each as a separate script/module.
- **Config-Driven:** All environment and pipeline settings are loaded from YAML config files.
- **Mock Data:** Use `mock-data/` for local/dev testing; pipeline switches automatically when `environment: develop`.
- **Documentation:**
  - Main index: `documentation/abstract.md`
  - Architecture: `documentation/architecture/architecture.md`
  - Testing: `documentation/testing/testing.md`
- **Common Utilities:** Place reusable code in `src/common/`.

## Conventions
- Keep modules small, focused, and well-tested.
- Follow the documentation structure for adding new docs or code.
- Prefer explicit, config-driven patterns over hardcoding paths or parameters.
- Use the provided loader for config merging—do not reimplement.

## Integration Points
- Embedding uses `sentence-transformers` (Python)
- Indexing uses Qdrant
- All scripts expect NDJSON and NPZ formats for data exchange

## Examples
- See `mock-data/` for sample input/output files
- See `src/tagging/` for main pipeline scripts

---
For more, see the documentation index at `documentation/abstract.md` and architecture at `documentation/architecture/architecture.md`.
