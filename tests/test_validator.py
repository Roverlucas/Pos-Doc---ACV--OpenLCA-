"""Tests for input validation."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from olca_cf_converter.validator import ValidationError, validate_excel


@pytest.fixture
def valid_excel(tmp_path):
    """Create a minimal valid Excel file."""
    df = pd.DataFrame({
        "Flow": ["Ammonia", "NOx", "SO2"],
        "Category": [
            "Elementary flows/Emission to air/unspecified",
            "Elementary flows/Emission to air/unspecified",
            "Elementary flows/Emission to air/high population density",
        ],
        "Factor": [0.00058, 0.00123, 0.00045],
        "Unit": ["DALY", "DALY", "DALY"],
        "Location": ["Brazil", "Brazil", "Brazil, São Paulo"],
    })
    path = tmp_path / "test.xlsx"
    df.to_excel(path, index=False)
    return path


def test_validate_valid_file(valid_excel):
    df = validate_excel(valid_excel)
    assert len(df) == 3
    assert "Flow" in df.columns


def test_validate_file_not_found():
    with pytest.raises(ValidationError, match="not found"):
        validate_excel("/nonexistent/file.xlsx")


def test_validate_wrong_extension(tmp_path):
    path = tmp_path / "test.csv"
    path.write_text("a,b,c")
    with pytest.raises(ValidationError, match="Expected .xlsx"):
        validate_excel(path)


def test_validate_missing_columns(tmp_path):
    df = pd.DataFrame({"Name": ["A"], "Value": [1.0]})
    path = tmp_path / "bad.xlsx"
    df.to_excel(path, index=False)
    with pytest.raises(ValidationError, match="Missing required columns"):
        validate_excel(path)


def test_validate_non_numeric_factor(tmp_path):
    df = pd.DataFrame({
        "Flow": ["Ammonia"],
        "Category": ["test"],
        "Factor": ["not_a_number"],
        "Unit": ["DALY"],
        "Location": ["Brazil"],
    })
    path = tmp_path / "bad_factor.xlsx"
    df.to_excel(path, index=False)
    with pytest.raises(ValidationError, match="Non-numeric"):
        validate_excel(path)


def test_validate_empty_flow_name(tmp_path):
    df = pd.DataFrame({
        "Flow": [""],
        "Category": ["test"],
        "Factor": [0.001],
        "Unit": ["DALY"],
        "Location": ["Brazil"],
    })
    path = tmp_path / "empty_flow.xlsx"
    df.to_excel(path, index=False)
    with pytest.raises(ValidationError, match="Empty flow"):
        validate_excel(path)
