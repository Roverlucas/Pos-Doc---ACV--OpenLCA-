"""Tests for the CLI interface."""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "olca_cf_converter.cli", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "convert" in result.stdout
    assert "validate" in result.stdout
    assert "init" in result.stdout


def test_cli_version():
    result = subprocess.run(
        [sys.executable, "-m", "olca_cf_converter.cli", "--version"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "1.0.0" in result.stdout


def test_cli_init(tmp_path):
    output = tmp_path / "test-config.yaml"
    result = subprocess.run(
        [sys.executable, "-m", "olca_cf_converter.cli", "init", "-o", str(output)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert output.exists()

    with open(output) as f:
        config = yaml.safe_load(f)
    assert "method" in config
    assert "category" in config
    assert "units" in config
    assert "files" in config
