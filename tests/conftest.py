"""Shared fixtures for pytest."""

import sys
from pathlib import Path
from typing import Generator

import pytest

# Make `src.*` importable no matter which directory pytest was invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def project_root() -> Path:
    """Return the absolute path to the project root."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def run_from_project_root(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run every test with the project root as the working directory.

    Makes the suite independent of the directory pytest was invoked from
    (the sys.path insert above covers the import side of the same issue).
    """
    monkeypatch.chdir(project_root)


@pytest.fixture
def template_dir(project_root: Path) -> Path:
    """Return the templates/ directory."""
    return project_root / "templates"


@pytest.fixture
def src_dir(project_root: Path) -> Path:
    """Return the src/ directory."""
    return project_root / "src"


@pytest.fixture
def config_dir(project_root: Path) -> Path:
    """Return the config/ directory."""
    return project_root / "config"


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """A temporary directory for writing test output."""
    return tmp_path / "output"


@pytest.fixture
def sample_css(tmp_path: Path) -> Path:
    """Create and return a minimal sample CSS file."""
    css_path = tmp_path / "sample.css"
    css_path.write_text(
        "body {\n"
        "  color: #333;\n"
        "  font-size: 14px;\n"
        "}\n"
        ".markdown-preview.markdown-preview h1 {\n"
        "  border-bottom: 1px solid #eee;\n"
        "}\n"
    )
    return css_path


@pytest.fixture
def codeblock_css(tmp_path: Path) -> Path:
    """Create and return a minimal code block theme CSS file."""
    css_path = tmp_path / "codeblock.css"
    css_path.write_text(
        ".markdown-preview pre {\n"
        "  background: #f5f5f5;\n"
        "  padding: 8px;\n"
        "}\n"
    )
    return css_path


@pytest.fixture
def config_json(config_dir: Path) -> Path:
    """Return the path to config.json (may not exist during tests)."""
    return config_dir / "config.json"