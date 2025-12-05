"""Tests for the organizer module."""

import json
import tempfile
from pathlib import Path

import pytest

from fs_cleaner.config import Config
from fs_cleaner.organizer import MoveOperation, Organizer
from fs_cleaner.scanner import DirectoryInfo, FileInfo
from datetime import datetime


@pytest.fixture
def temp_dir():
    """Create a temporary directory for target files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_app_dir():
    """Create a temporary directory for app data (plans, etc.)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files():
    """Create sample FileInfo objects."""
    return [
        FileInfo(
            name="doc.pdf",
            path=Path("/test/doc.pdf"),
            size=1000,
            modified=datetime.now(),
            extension=".pdf",
            relative_path="doc.pdf",
        ),
        FileInfo(
            name="image.png",
            path=Path("/test/image.png"),
            size=2000,
            modified=datetime.now(),
            extension=".png",
            relative_path="image.png",
        ),
    ]


@pytest.fixture
def sample_directories():
    """Create sample DirectoryInfo objects."""
    return [
        DirectoryInfo(
            name="project",
            path=Path("/test/project"),
            modified=datetime.now(),
            item_count=5,
            sample_contents=["main.py", "README.md"],
            relative_path="project",
        ),
    ]


def test_create_move_plan(temp_dir, temp_app_dir, sample_files, sample_directories):
    """Test move plan creation."""
    config = Config(target_dir=temp_dir, _app_dir=temp_app_dir)
    organizer = Organizer(config)

    file_classifications = {
        "Documents": ["doc.pdf"],
        "Images": ["image.png"],
    }
    dir_classifications = {
        "Development": ["project"],
    }

    moves = organizer.create_move_plan(
        sample_files,
        sample_directories,
        file_classifications,
        dir_classifications,
    )

    assert len(moves) == 3

    # Check file moves
    doc_move = next(m for m in moves if m.name == "doc.pdf")
    assert doc_move.category == "Documents"
    assert doc_move.item_type == "file"
    assert "Files/Documents" in str(doc_move.destination)

    # Check directory move
    project_move = next(m for m in moves if m.name == "project")
    assert project_move.category == "Development"
    assert project_move.item_type == "directory"
    assert "Folders/Development" in str(project_move.destination)


def test_move_operation_serialization():
    """Test MoveOperation to/from dict."""
    move = MoveOperation(
        item_type="file",
        name="test.txt",
        source=Path("/source/test.txt"),
        destination=Path("/dest/test.txt"),
        category="Documents",
    )

    data = move.to_dict()
    restored = MoveOperation.from_dict(data)

    assert restored.item_type == move.item_type
    assert restored.name == move.name
    assert restored.source == move.source
    assert restored.destination == move.destination
    assert restored.category == move.category


def test_save_and_load_plan(temp_dir, temp_app_dir, sample_files, sample_directories):
    """Test saving and loading move plans."""
    config = Config(target_dir=temp_dir, _app_dir=temp_app_dir)
    organizer = Organizer(config)

    file_classifications = {"Documents": ["doc.pdf"]}
    dir_classifications = {}

    moves = organizer.create_move_plan(
        sample_files,
        sample_directories,
        file_classifications,
        dir_classifications,
    )

    # Save plan
    organizer.save_plan(moves)
    assert config.plan_file.exists()

    # Load plan
    loaded_moves = organizer.load_plan()
    assert len(loaded_moves) == len(moves)
    assert loaded_moves[0].name == moves[0].name


def test_load_plan_missing_file(temp_dir, temp_app_dir):
    """Test loading plan when file doesn't exist."""
    config = Config(target_dir=temp_dir, _app_dir=temp_app_dir)
    organizer = Organizer(config)

    with pytest.raises(FileNotFoundError):
        organizer.load_plan()


def test_dry_run_does_not_move(temp_dir, temp_app_dir, capsys):
    """Test that dry run doesn't move files."""
    config = Config(target_dir=temp_dir, _app_dir=temp_app_dir)
    organizer = Organizer(config, verbose=True)

    # Create a test file
    test_file = temp_dir / "test.txt"
    test_file.touch()

    moves = [
        MoveOperation(
            item_type="file",
            name="test.txt",
            source=test_file,
            destination=temp_dir / "_Organized" / "Files" / "test.txt",
            category="Documents",
        )
    ]

    success, errors = organizer.execute_moves(moves, dry_run=True)

    # File should still be in original location
    assert test_file.exists()
    assert not (temp_dir / "_Organized").exists()

    # Check output mentions dry run
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
