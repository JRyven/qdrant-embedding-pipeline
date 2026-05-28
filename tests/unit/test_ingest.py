import json
import sys
from pathlib import Path


def test_ingest_creates_ndjson(tmp_path, monkeypatch):
    # create sample markdown
    md = tmp_path / "sample.md"
    md.write_text("""---\ntitle: t\n---\n\nThis is a test document for ingest.""")

    out = tmp_path / "out.ndjson"
    monkeypatch.setattr(sys, "argv", ["ingest", "--root", str(tmp_path), "--out", str(out)])

    # import and run the ingest main
    from src.tagging import ingest

    ingest.main()

    assert out.exists()
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    obj = json.loads(lines[0])
    assert "text" in obj and "source_path" in obj
