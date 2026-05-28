#!/usr/bin/env python3
"""Example: load and print the merged tagging-pipeline configuration."""

from pathlib import Path
import json

from src.tagging.config_loader import load_config


if __name__ == "__main__":
    config = load_config(Path("config"))
    print(json.dumps(config, indent=2))
