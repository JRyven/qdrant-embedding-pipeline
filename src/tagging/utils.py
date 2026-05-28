from pathlib import Path
from typing import Optional, Tuple, List
import json
import sqlite3
import numpy as np


def read_frontmatter(path: Path) -> Tuple[Optional[str], str, List[str]]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1].strip()
            body = parts[2].lstrip("\n")
            tags: List[str] = []
            for line in fm.splitlines():
                if line.strip().startswith("tags:"):
                    try:
                        val = line.split(":", 1)[1].strip()
                        if val.startswith("["):
                            tags = json.loads(val.replace("'", '"'))
                    except Exception:
                        pass
            return fm, body, tags
    return None, text, []


def write_markdown_with_tags(src: Path, dest: Path, tags: List[str]):
    fm, body, _ = read_frontmatter(src)
    if fm is None:
        fm_text = "---\n"
        fm_text += f"tags: {json.dumps(tags)}\n"
        fm_text += "---\n\n"
    else:
        lines = fm.splitlines()
        out = []
        replaced = False
        for line in lines:
            if line.strip().startswith("tags:"):
                out.append(f"tags: {json.dumps(tags)}")
                replaced = True
            else:
                out.append(line)
        if not replaced:
            out.append(f"tags: {json.dumps(tags)}")
        fm_text = "---\n" + "\n".join(out) + "\n---\n\n"
    dest.write_text(fm_text + body, encoding="utf-8")


def load_embeddings_and_meta(smoke_dir: Path):
    embf = smoke_dir / "embeddings.npz"
    metaf = smoke_dir / "embeddings_meta.ndjson"
    if not embf.exists() or not metaf.exists():
        raise FileNotFoundError("Missing embeddings or metadata ndjson under smoke dir")
    arr = np.load(embf)
    embeddings = arr["embeddings"].astype("float32")
    metas = []
    with metaf.open(encoding="utf-8") as fh:
        for line in fh:
            metas.append(json.loads(line))
    return embeddings, metas


def build_qdrant_index(embeddings, collection_name="default", qdrant_url="http://localhost:6333"):
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, VectorParams, Distance
    except Exception:
        raise
    client = QdrantClient(url=qdrant_url)
    dim = embeddings.shape[1]
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    # Assuming embeddings are list of vectors, but need ids and payloads
    # For now, dummy
    points = [PointStruct(id=i, vector=emb.tolist()) for i, emb in enumerate(embeddings)]
    client.upsert(collection_name=collection_name, points=points)
    return client


def connect_metadata_db(smoke_dir: Path):
    dbf = smoke_dir / "metadata.sqlite"
    if not dbf.exists():
        return None
    conn = sqlite3.connect(str(dbf))
    return conn


def get_source_path_for_row(conn: sqlite3.Connection, rowidx: int):
    cur = conn.cursor()
    cur.execute("SELECT source_path FROM documents WHERE rowid = ?", (rowidx + 1,))
    row = cur.fetchone()
    return row[0] if row else None
