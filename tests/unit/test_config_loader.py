from pathlib import Path

from src.tagging.config_loader import load_config


def test_load_config_develop_defaults():
    cfg = load_config(Path("config"))
    assert cfg.get("environment") == "develop"
    # develop config should point to mock-data paths
    assert "mock-data" in cfg.get("paths", {}).get("ingest_ndjson", "")
