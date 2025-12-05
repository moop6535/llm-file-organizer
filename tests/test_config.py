"""Tests for the config module."""

from pathlib import Path

import pytest

from fs_cleaner.config import Config


def test_default_config():
    """Test default configuration values."""
    config = Config()

    assert config.target_dir == Path.cwd()
    assert config.llm_provider == "openai"
    assert config.batch_size == 50
    assert config.skip_hidden is True
    assert config.scan_depth == 0
    assert config.organize_directories is True


def test_custom_target_dir():
    """Test custom target directory."""
    config = Config(target_dir=Path("/custom/path"))

    assert config.target_dir == Path("/custom/path")
    assert config.output_dir == Path("/custom/path/_Organized")


def test_custom_output_dir():
    """Test custom output directory."""
    config = Config(
        target_dir=Path("/source"),
        output_dir=Path("/destination"),
    )

    assert config.output_dir == Path("/destination")


def test_default_models():
    """Test default models for each provider."""
    assert Config.default_model_for_provider("openai") == "gpt-4o-mini"
    assert Config.default_model_for_provider("anthropic") == "claude-sonnet-4-20250514"
    assert Config.default_model_for_provider("ollama") == "llama3.2"


def test_auto_model_selection():
    """Test that model is auto-selected based on provider."""
    config = Config(llm_provider="anthropic")
    assert config.llm_model == "claude-sonnet-4-20250514"

    config = Config(llm_provider="ollama")
    assert config.llm_model == "llama3.2"


def test_custom_model():
    """Test custom model override."""
    config = Config(llm_provider="openai", llm_model="gpt-4-turbo")
    assert config.llm_model == "gpt-4-turbo"


def test_path_properties():
    """Test path property methods."""
    config = Config(target_dir=Path("/test"))

    # Plans are stored in ~/.fs-cleaner/plans/<target_slug>/
    expected_base = Path.home() / ".fs-cleaner" / "plans" / "test"
    assert config.config_dir == expected_base
    assert config.undo_file == expected_base / "undo_log.json"

    # Plan files are timestamped
    plan_file = config.get_timestamped_plan_file("20240115_120000")
    assert plan_file == expected_base / "plan_20240115_120000.json"


def test_skip_items_default():
    """Test default skip items."""
    config = Config()

    assert ".DS_Store" in config.skip_items
    assert ".localized" in config.skip_items
    assert ".env" in config.skip_items
    assert ".git" in config.skip_items
    assert "node_modules" in config.skip_items


def test_custom_skip_items():
    """Test custom skip items."""
    config = Config(skip_items={"custom_skip"})

    assert "custom_skip" in config.skip_items
    assert ".DS_Store" not in config.skip_items
