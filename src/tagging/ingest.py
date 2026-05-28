#!/usr/bin/env python3
"""Simple ingest script: discovers markdown files, strips YAML frontmatter, chunks text, emits NDJSON."""
import argparse
import json
from pathlib import Path
import re


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text


def chunk_text(text: str, max_words: int = 200):
    words = text.split()
    for i in range(0, len(words), max_words):
        yield " ".join(words[i : i + max_words])


def iterate_markdown(root: Path):
    for p in sorted(root.rglob("*.md")):
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        body = strip_frontmatter(text)
        # Remove developer-added "Shared words:" lines from the body
        # to avoid skewing embeddings or lexical matches. Case-insensitive.
        lines = body.splitlines()
        filtered = [l for l in lines if not l.strip().lower().startswith("shared words:")]
        body = "\n".join(filtered).strip()
        yield p, body


def main():
    parser = argparse.ArgumentParser(description="Ingest markdown and produce NDJSON chunks")
    parser.add_argument("--root", required=True, help="Root dir to scan")
    parser.add_argument("--out", required=True, help="Output NDJSON file")
    parser.add_argument("--chunk-words", type=int, default=200)
    args = parser.parse_args()

    root = Path(args.root)
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    with outp.open("w", encoding="utf-8") as fh:
        doc_id = 0
        for p, body in iterate_markdown(root):
            for idx, chunk in enumerate(chunk_text(body, args.chunk_words)):
                item = {
                    "id": f"doc-{doc_id}",
                    "source_path": str(p),
                    "chunk_id": idx,
                    "text": chunk,
                }
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                doc_id += 1


if __name__ == "__main__":
    main()
