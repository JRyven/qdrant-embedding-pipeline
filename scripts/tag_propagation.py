#!/usr/bin/env python3
"""Tagging by propagation from nearest neighbors' frontmatter tags."""
from pathlib import Path
import json
import sys

# ensure src/ is importable when running from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tagging.utils import (
    read_frontmatter,
    write_markdown_with_tags,
    load_embeddings_and_meta,
    build_qdrant_index,
    connect_metadata_db,
    get_source_path_for_row,
)


def main():
    ROOT = Path(".")
    smoke = ROOT / "data" / "smoke"
    embf = smoke / "embeddings.npz"
    meta = smoke / "embeddings_meta.ndjson"
    dbf = smoke / "metadata.sqlite"
    outdir = Path("mock-results-propagation")
    outdir.mkdir(exist_ok=True)

    if not embf.exists() or not meta.exists() or not dbf.exists():
        print("Missing smoke artifacts under data/smoke. Run scripts/run_smoke_local.sh first.")
        sys.exit(1)

    import numpy as np

    embeddings, metas = load_embeddings_and_meta(smoke)
    client = build_qdrant_index(embeddings, "prop-collection")
    conn = connect_metadata_db(smoke)

    # For each item, gather neighbor tags and set tags to most common neighbors
    import collections

    k = min(5, len(metas))
    for i, rec in enumerate(metas):
        results = client.search(collection_name="prop-collection", query_vector=embeddings[i].tolist(), limit=k)
        # collect neighbor tags (skip self)
        neigh = [hit.id for hit in results if hit.id != i]
        tags = []
        for n in neigh:
            src_path = None
            if conn is not None:
                src_path = get_source_path_for_row(conn, int(n))
            if src_path:
                p = Path(src_path)
                if p.exists():
                    _, _, t = read_frontmatter(p)
                    tags.extend(t)
        # dedupe and keep order by frequency
        if tags:
            counts = collections.Counter(tags)
            chosen = [t for t, _ in counts.most_common(3)]
        else:
            chosen = []

        src = Path(rec.get("source_path"))
        dest = outdir / src.name
        write_markdown_with_tags(src, dest, chosen)

    conn.close()
    print("Propagation tagging complete ->", outdir)


if __name__ == "__main__":
    main()
