from src.tagging.ingest import strip_frontmatter, chunk_text, iterate_markdown


def test_strip_frontmatter():
    text = """---\nkey: value\n---\nHello world"""
    assert strip_frontmatter(text).startswith("Hello world")


def test_chunk_text():
    s = "one two three four five six"
    chunks = list(chunk_text(s, max_words=2))
    assert chunks == ["one two", "three four", "five six"]


def test_iterate_markdown_reads_sample(tmp_path, monkeypatch):
    # create a temporary directory with a markdown file and ensure iterate_markdown finds it
    p = tmp_path / "sample.md"
    p.write_text("---\ntitle: t\n---\nSample body text here.")

    results = list(iterate_markdown(tmp_path))
    assert len(results) == 1
    path, body = results[0]
    assert path.name == "sample.md"
    assert "Sample body text" in body
