import sys
from pathlib import Path
import pytest

# Ensure repository root is on sys.path for imports like `src.tagging` during tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def project_root():
    return ROOT


@pytest.fixture
def mock_data_dir(project_root):
    return project_root / "mock-data"


@pytest.fixture
def sample_markdown(mock_data_dir):
    p = mock_data_dir / "sample1.md"
    return p
