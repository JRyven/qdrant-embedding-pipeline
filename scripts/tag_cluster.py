#!/usr/bin/env python3
"""Tagging by clustering embeddings (simple k-means) and assigning cluster labels."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tagging.utils import read_frontmatter, write_markdown_with_tags, load_embeddings_and_meta


def kmeans(X, k=3, iters=50):
    import numpy as np

    n, d = X.shape
    # init centers with first k points (deterministic)
    centers = X[:k].copy()
    for _ in range(iters):
        # assign
        dists = ((X[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = dists.argmin(axis=1)
        new_centers = np.zeros_like(centers)
        for i in range(k):
            if (labels == i).any():
                new_centers[i] = X[labels == i].mean(axis=0)
            else:
                new_centers[i] = centers[i]
        if np.allclose(new_centers, centers):
            break
        centers = new_centers
    return labels, centers


def main():
    ROOT = Path(".")
    smoke = ROOT / "data" / "smoke"
    embf = smoke / "embeddings.npz"
    meta = smoke / "embeddings_meta.ndjson"
    outdir = Path("mock-results-cluster")
    outdir.mkdir(exist_ok=True)

    if not embf.exists() or not meta.exists():
        print("Missing smoke artifacts under data/smoke. Run scripts/run_smoke_local.sh first.")
        sys.exit(1)

    import numpy as np

    embeddings, metas = load_embeddings_and_meta(smoke)

    n = embeddings.shape[0]
    k = min(3, max(1, n // 2))
    labels, centers = kmeans(embeddings, k=k)

    # assign cluster tags
    for i, m in enumerate(metas):
        src = Path(m.get("source_path"))
        dest = outdir / src.name
        tag = f"cluster-{int(labels[i])}"
        # preserve existing tags + cluster tag
        _, _, t = read_frontmatter(src)
        new_tags = list(dict.fromkeys((t or []) + [tag]))
        write_markdown_with_tags(src, dest, new_tags)

    print("Clustering tagging complete ->", outdir)


if __name__ == "__main__":
    main()
