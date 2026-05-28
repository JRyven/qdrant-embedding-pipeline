#!/usr/bin/env python3
"""Tagging by k-NN classifier trained on labeled frontmatter tags."""
from pathlib import Path
import json
import sys

# make src/ importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tagging.utils import (
    read_frontmatter,
    write_markdown_with_tags,
    load_embeddings_and_meta,
)


def main():
    ROOT = Path(".")
    smoke = ROOT / "data" / "smoke"
    embf = smoke / "embeddings.npz"
    meta = smoke / "embeddings_meta.ndjson"
    dbf = smoke / "metadata.sqlite"
    outdir = Path("mock-results-k-nn")
    outdir.mkdir(exist_ok=True)

    if not embf.exists() or not meta.exists() or not dbf.exists():
        print("Missing smoke artifacts under data/smoke. Run scripts/run_smoke_local.sh first.")
        sys.exit(1)

    import numpy as np

    embeddings, metas = load_embeddings_and_meta(smoke)

    # build labeled set: use first tag of those that have tags
    labeled_idx = []
    labels = []
    for i, m in enumerate(metas):
        p = Path(m.get("source_path"))
        if p.exists():
            _, _, t = read_frontmatter(p)
            if t:
                labeled_idx.append(i)
                labels.append(t[0])

    if not labeled_idx:
        print("No labeled items found in frontmatter; k-NN requires at least one labeled sample.")
        # fallback: copy originals
        for m in metas:
            src = Path(m.get("source_path"))
            dest = outdir / src.name
            write_markdown_with_tags(src, dest, [])
        return

    labeled_emb = embeddings[labeled_idx]

    # classify unlabeled by nearest labeled neighbor (majority vote among k)
    from collections import Counter

    def classify(vec, k=3):
        # compute L2 distances to labeled_emb
        d = ((labeled_emb - vec) ** 2).sum(axis=1)
        idxs = d.argsort()[:k]
        votes = [labels[j] for j in idxs]
        return Counter(votes).most_common(1)[0][0]

    for i, m in enumerate(metas):
        src = Path(m.get("source_path"))
        dest = outdir / src.name
        # if has tags, keep existing tags
        _, _, t = read_frontmatter(src)
        if t:
            write_markdown_with_tags(src, dest, t)
        else:
            tag = classify(embeddings[i])
            write_markdown_with_tags(src, dest, [tag])

    print("k-NN tagging complete ->", outdir)


if __name__ == "__main__":
    main()
