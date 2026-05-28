#!/usr/bin/env python3
"""Tagging using LLM-like heuristics: keyword extraction + neighbor-context summarization.

This is a deterministic fallback that simulates an LLM by combining keyword heuristics
and nearest-neighbor tag evidence. If you have an LLM integration, this script can be
adapted to call the model and use neighbors as context.
"""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tagging.utils import (
    read_frontmatter,
    write_markdown_with_tags,
    load_embeddings_and_meta,
    build_qdrant_index,
    connect_metadata_db,
    get_source_path_for_row,
)


def extract_keywords(text: str):
    # very small heuristic keyword extractor
    kws = []
    txt = text.lower()
    candidates = ["sample", "test", "mock", "short", "embedding", "index", "qdrant", "ingest"]
    for c in candidates:
        if c in txt:
            kws.append(c)
    return kws[:3]


def main():
    ROOT = Path(".")
    smoke = ROOT / "data" / "smoke"
    embf = smoke / "embeddings.npz"
    meta = smoke / "embeddings_meta.ndjson"
    dbf = smoke / "metadata.sqlite"
    outdir = Path("mock-results-LLM")
    outdir.mkdir(exist_ok=True)

    if not embf.exists() or not meta.exists() or not dbf.exists():
        print("Missing smoke artifacts under data/smoke. Run scripts/run_smoke_local.sh first.")
        sys.exit(1)

    import numpy as np

    embeddings, metas = load_embeddings_and_meta(smoke)
    client = build_qdrant_index(embeddings, "tag-collection")
    conn = connect_metadata_db(smoke)

    k = 3
    # For each embedding, search neighbors
    I = []
    D = []
    for emb in embeddings:
        results = client.search(collection_name="tag-collection", query_vector=emb.tolist(), limit=k+1)  # +1 to exclude self
        neighbors = [hit.id for hit in results if hit.id != len(I)]  # approximate
        distances = [hit.score for hit in results]
        I.append(neighbors[:k])
        D.append(distances[:k])

    for i, m in enumerate(metas):
        src = Path(m.get("source_path"))
        dest = outdir / src.name
        body = src.read_text(encoding="utf-8")
        _, body_text = None, body
        # extract keywords
        kws = extract_keywords(body_text)

        # neighbor evidence
        neigh = [j for j in I[i].tolist() if j != i]
        neigh_tags = []
        for n in neigh:
            src_path = None
            if conn is not None:
                src_path = get_source_path_for_row(conn, int(n))
            if src_path:
                p = Path(src_path)
                if p.exists():
                    _, _, t = read_frontmatter(p)
                    neigh_tags.extend(t)

        # combine heuristics: neighbor tags then keywords
        combined = []
        for t in neigh_tags:
            if t not in combined:
                combined.append(t)
        for k_ in kws:
            if k_ not in combined:
                combined.append(k_)

        # ensure compact result
        result_tags = combined[:4]
        write_markdown_with_tags(src, dest, result_tags)

    conn.close()
    print("LLM-like tagging complete ->", outdir)


if __name__ == "__main__":
    main()
