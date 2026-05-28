#!/usr/bin/env python3
"""Build a Qdrant index from embeddings and write a sqlite metadata mapping."""
import argparse
from pathlib import Path
import numpy as np
import json
import sqlite3


def load_meta(ndjson_path: Path):
    meta = []
    with ndjson_path.open(encoding="utf-8") as fh:
        for line in fh:
            meta.append(json.loads(line))
    return meta


def main():
    parser = argparse.ArgumentParser(description="Build Qdrant index and metadata DB")
    parser.add_argument("--emb", required=True, help=".npz file with embeddings")
    parser.add_argument("--meta", required=True, help="NDJSON meta file")
    parser.add_argument("--collection", required=True, help="Qdrant collection name")
    parser.add_argument("--db", required=True, help="Output sqlite DB path")
    parser.add_argument("--qdrant-url", default="http://localhost:6333", help="Qdrant service URL")
    parser.add_argument("--qdrant-location", default=None, help="Qdrant local location, e.g. :memory:")
    args = parser.parse_args()

    embf = Path(args.emb)
    meta_path = Path(args.meta)
    collection_name = args.collection
    db_path = Path(args.db)
    qdrant_url = args.qdrant_url
    qdrant_location = args.qdrant_location

    data = np.load(embf)
    embeddings = data["embeddings"]

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, VectorParams, Distance
    except Exception:
        print("Missing dependency: install `qdrant-client`. See requirements.txt")
        raise

    client = QdrantClient(location=qdrant_location) if qdrant_location else QdrantClient(url=qdrant_url)

    # Create collection if not exists
    dim = embeddings.shape[1]
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    meta = load_meta(meta_path)
    points = []
    for i, m in enumerate(meta):
        point = PointStruct(
            id=i,  # or use m.get("id") if unique
            vector=embeddings[i].tolist(),
            payload=m
        )
        points.append(point)

    client.upsert(collection_name=collection_name, points=points)
    # Ensure a fresh DB file so repeated runs don't append duplicate rows
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS documents (rowid INTEGER PRIMARY KEY, doc_id TEXT, source_path TEXT, chunk_id INTEGER, text_snippet TEXT)"
    )
    cur.executemany(
        "INSERT INTO documents (doc_id, source_path, chunk_id, text_snippet) VALUES (?, ?, ?, ?)",
        [(m.get("id"), m.get("source_path"), m.get("chunk_id"), (m.get("text") or "")[:200]) for m in meta],
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
