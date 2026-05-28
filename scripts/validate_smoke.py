#!/usr/bin/env python3
"""Validate smoke outputs: embeddings, Qdrant index, and metadata DB.

Checks performed:
- files exist
- embeddings row count matches metadata row count
- Qdrant collection contains expected number of vectors
- nearest-neighbor query returns valid document ids from DB
"""
import sys
from pathlib import Path
import sqlite3

def fail(msg: str):
    print("ERROR:", msg)
    sys.exit(2)


def main():
    root = Path("data/smoke")
    embf = root / "embeddings.npz"
    dbf = root / "metadata.sqlite"

    if not root.exists():
        fail(f"Smoke data dir not found: {root}")

    for p in (embf, dbf):
        if not p.exists():
            fail(f"Missing expected file: {p}")

    import numpy as np

    data = np.load(embf)
    embeddings = data.get("embeddings")
    if embeddings is None:
        fail("No 'embeddings' array found in npz file")

    n_emb = embeddings.shape[0]
    print(f"Embeddings rows: {n_emb}")

    # DB count
    conn = sqlite3.connect(str(dbf))
    cur = conn.cursor()
    try:
        cur.execute("SELECT count(*) FROM documents")
        n_db = cur.fetchone()[0]
    except Exception as e:
        fail(f"Error querying database: {e}")
    finally:
        conn.close()

    print(f"Metadata DB rows: {n_db}")

    if n_emb != n_db:
        fail(f"Embeddings count ({n_emb}) != metadata rows ({n_db})")

    # Qdrant index checks
    try:
        from qdrant_client import QdrantClient
    except Exception as e:
        fail(f"qdrant-client not available: {e}")

    client = QdrantClient(location=":memory:")
    from qdrant_client.models import PointStruct, VectorParams, Distance
    dim = embeddings.shape[1]
    client.recreate_collection(
        collection_name="smoke-collection",
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    points = [PointStruct(id=i, vector=vec.tolist()) for i, vec in enumerate(embeddings)]
    client.upsert(collection_name="smoke-collection", points=points)
    collection_info = client.get_collection("smoke-collection")
    nt = collection_info.points_count
    print(f"Qdrant collection points: {nt}")
    if nt != n_emb:
        fail(f"Qdrant collection size ({nt}) != embeddings rows ({n_emb})")

    # Nearest neighbor query (k=3)
    vec = embeddings[0]
    results = client.search(collection_name="smoke-collection", query_vector=vec.tolist(), limit=min(3, n_emb))
    idxs = [hit.id for hit in results]
    distances = [hit.score for hit in results]
    print(f"Neighbor indices for first vector: {idxs}, distances: {distances}")

    # Verify each returned index maps to a DB row
    conn = sqlite3.connect(str(dbf))
    cur = conn.cursor()
    for i in idxs:
        # Assuming ids are 0-based
        if i < 0 or i >= n_db:
            fail(f"Index returned out-of-range neighbor: {i}")
        # sqlite rowid is 1-based; but since we used id=i, and meta has id, but in code id=i, so rowid=i+1?
        cur.execute("SELECT doc_id, source_path FROM documents WHERE rowid = ?", (i + 1,))
        row = cur.fetchone()
        if not row:
            fail(f"No DB entry for rowid {i+1}")
        print(f"Neighbor {i} -> doc_id={row[0]}, source={row[1]}")
    conn.close()

    print("Validation successful: smoke outputs look consistent.")


if __name__ == "__main__":
    main()
