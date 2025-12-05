"""Tests for the scanner module."""

import tempfile
from pathlib import Path

import pytest

from llm_file_organizer.config import Config
from llm_file_organizer.scanner import Scanner


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create some test files
        (base / "document.pdf").touch()
        (base / "image.png").touch()
        (base / "script.py").touch()

        # Create some test directories
        (base / "project").mkdir()
        (base / "project" / "main.py").touch()
        (base / "project" / "README.md").touch()

        (base / "photos").mkdir()
        (base / "photos" / "vacation.jpg").touch()

        # Create hidden file (should be skipped by default)
        (base / ".hidden").touch()
        (base / ".DS_Store").touch()

        yield base


def test_scanner_finds_files(temp_dir):
    """Test that scanner finds all non-hidden files."""
    config = Config(target_dir=temp_dir)
    scanner = Scanner(config)

    files, directories = scanner.scan()

    file_names = {f.name for f in files}
    assert "document.pdf" in file_names
    assert "image.png" in file_names
    assert "script.py" in file_names
    assert ".hidden" not in file_names
    assert ".DS_Store" not in file_names


def test_scanner_finds_directories(temp_dir):
    """Test that scanner finds directories with sample contents."""
    config = Config(target_dir=temp_dir)
    scanner = Scanner(config)

    files, directories = scanner.scan()

    dir_names = {d.name for d in directories}
    assert "project" in dir_names
    assert "photos" in dir_names

    # Check sample contents
    project_dir = next(d for d in directories if d.name == "project")
    assert project_dir.item_count == 2
    assert "main.py" in project_dir.sample_contents


def test_scanner_respects_skip_items(temp_dir):
    """Test that scanner respects skip_items configuration."""
    config = Config(
        target_dir=temp_dir,
        skip_items={"document.pdf", "project"},
    )
    scanner = Scanner(config)

    files, directories = scanner.scan()

    file_names = {f.name for f in files}
    dir_names = {d.name for d in directories}

    assert "document.pdf" not in file_names
    assert "project" not in dir_names
    assert "image.png" in file_names
    assert "photos" in dir_names


def test_scanner_handles_missing_directory():
    """Test that scanner raises error for missing directory."""
    config = Config(target_dir=Path("/nonexistent/path"))
    scanner = Scanner(config)

    with pytest.raises(FileNotFoundError):
        scanner.scan()


def test_file_info_to_dict(temp_dir):
    """Test FileInfo serialization."""
    config = Config(target_dir=temp_dir)
    scanner = Scanner(config)

    files, _ = scanner.scan()
    file_info = files[0]
    data = file_info.to_dict()

    assert "name" in data
    assert "path" in data
    assert "size" in data
    assert "modified" in data
    assert "extension" in data


def test_directory_info_to_dict(temp_dir):
    """Test DirectoryInfo serialization."""
    config = Config(target_dir=temp_dir)
    scanner = Scanner(config)

    _, directories = scanner.scan()
    dir_info = directories[0]
    data = dir_info.to_dict()

    assert "name" in data
    assert "path" in data
    assert "modified" in data
    assert "item_count" in data
    assert "sample_contents" in data
