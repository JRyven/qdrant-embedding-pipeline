#!/usr/bin/env python3
"""Embed NDJSON texts using sentence-transformers (fallback: instruct to install)."""
import argparse
import json
from pathlib import Path
import numpy as np
from tqdm import tqdm


def load_lines(path: Path):
    items = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            items.append(json.loads(line))
    return items


def main():
    parser = argparse.ArgumentParser(description="Compute embeddings for NDJSON input")
    parser.add_argument("--in", dest="inp", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock embeddings (no heavy deps)")
    parser.add_argument("--dim", type=int, default=8, help="Embedding dimension for mock mode")
    parser.add_argument("--model", default="all-MiniLM-L6-v2")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    inp = Path(args.inp)
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    items = load_lines(inp)
    texts = [it.get("text", "") for it in items]
    if args.mock:
        # Deterministic mock embeddings: hash text to bytes and convert to float vector
        import hashlib

        def text_to_vec(t, dim):
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # Expand or truncate to required dim by repeating the hash
            b = (h * ((dim // len(h)) + 1))[:dim]
            arr = np.frombuffer(b, dtype="u1").astype("float32")
            # normalize
            arr = arr / (arr.max() if arr.max() > 0 else 1.0)
            return arr.astype("float32")

        emb = np.vstack([text_to_vec(t, args.dim) for t in texts]).astype("float32")
        np.savez_compressed(outp, embeddings=emb)
    else:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            print("Missing dependency: install `sentence-transformers`. See requirements.txt")
            raise

        model = SentenceTransformer(args.model)
        emb = model.encode(texts, batch_size=args.batch_size, show_progress_bar=True)
        emb = np.asarray(emb, dtype=np.float32)
        np.savez_compressed(outp, embeddings=emb)

    # write companion NDJSON with same ordering (no-op copy)
    meta_out = outp.with_name(outp.stem + "_meta.ndjson")
    with meta_out.open("w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
