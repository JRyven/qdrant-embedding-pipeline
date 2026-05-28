import json
import sys
from pathlib import Path

import pytest


def test_embed_skippable(tmp_path, monkeypatch):
    pytest.importorskip("sentence_transformers")
    nd = tmp_path / "in.ndjson"
    nd.write_text(json.dumps({"id": "a", "text": "hello world"}) + "\n")
    out = tmp_path / "emb.npz"
    monkeypatch.setattr(sys, "argv", ["embed", "--in", str(nd), "--out", str(out)])
    from src.tagging import embed

    embed.main()
    assert out.exists()


def test_index_skippable(tmp_path, monkeypatch):
    pytest.importorskip("qdrant_client")
    import numpy as np

    emb = np.random.rand(2, 8).astype("float32")
    embf = tmp_path / "emb.npz"
    np.savez_compressed(embf, embeddings=emb)
    meta = tmp_path / "meta.ndjson"
    meta.write_text(json.dumps({"id": "a", "text": "hello"}) + "\n")
    collection = "test-collection"
    db = tmp_path / "meta.sqlite"
    monkeypatch.setattr(sys, "argv", [
        "index",
        "--emb",
        str(embf),
        "--meta",
        str(meta),
        "--collection",
        collection,
        "--db",
        str(db),
    ])
    from src.tagging import index_qdrant

    index_qdrant.main()
    assert db.exists()
