#!/usr/bin/env python3
"""Create persistent mock-results by copying `mock-data/` files, injecting a test tag, and running ingest."""
from pathlib import Path
import yaml
import shutil
import sys
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "mock-data"
OUT = ROOT / "mock-results"


def inject_tag_and_copy(src: Path, dst: Path):
    text = src.read_text(encoding="utf-8")
    if text.lstrip().startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            fm = yaml.safe_load(fm_text) or {}
            tags = fm.get("tags", []) or []
            if "test-generated" not in tags:
                tags.append("test-generated")
            fm["tags"] = tags
            fm["generated_at"] = datetime.utcnow().isoformat() + "Z"
            new_fm = "---\n" + yaml.safe_dump(fm, sort_keys=False).strip() + "\n---\n\n"
            dst.write_text(new_fm + body, encoding="utf-8")
            return
    # no frontmatter: prepend one
    fm = {"tags": ["test-generated"], "generated_at": datetime.utcnow().isoformat() + "Z"}
    new_fm = "---\n" + yaml.safe_dump(fm, sort_keys=False).strip() + "\n---\n\n"
    dst.write_text(new_fm + text, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for p in sorted(MOCK.glob("*.md")):
        dst = OUT / p.name
        inject_tag_and_copy(p, dst)

    # Run ingest to produce NDJSON in mock-results
    try:
        # import ingest by path: add project root to sys.path
        sys.path.insert(0, str(ROOT))
        from src.tagging import ingest

        old_argv = sys.argv[:]
        sys.argv = ["ingest", "--root", str(OUT), "--out", str(OUT / "ingest.ndjson"), "--chunk-words", "200"]
        ingest.main()
        sys.argv = old_argv
    except Exception as exc:
        print("Warning: ingest step failed:", exc)
    finally:
        # clean up sys.path insertion
        try:
            sys.path.remove(str(ROOT))
        except Exception:
            pass

    print("mock-results generated at:", OUT)


if __name__ == "__main__":
    main()
