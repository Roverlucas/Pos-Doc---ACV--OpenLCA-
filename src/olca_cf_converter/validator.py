"""
Input validation for Excel files and YAML configs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS_DEFAULT = ["Flow", "Category", "Factor", "Unit", "Location"]


class ValidationError(Exception):
    pass


def validate_excel(
    path: str | Path,
    required_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Validate and load an Excel file with characterization factors."""
    path = Path(path)
    cols = required_columns or REQUIRED_COLUMNS_DEFAULT

    if not path.exists():
        raise ValidationError(f"File not found: {path}")

    if path.suffix not in (".xlsx", ".xls"):
        raise ValidationError(f"Expected .xlsx or .xls, got: {path.suffix}")

    try:
        df = pd.read_excel(path)
    except Exception as e:
        raise ValidationError(f"Cannot read Excel file: {e}") from e

    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValidationError(
            f"Missing required columns: {missing}. "
            f"Found: {list(df.columns)}. "
            f"Expected: {cols}"
        )

    factor_col = cols[2]  # "Factor" by default
    non_numeric = df[~df[factor_col].apply(lambda x: isinstance(x, (int, float)))]
    if len(non_numeric) > 0:
        raise ValidationError(
            f"Non-numeric values in '{factor_col}' column at rows: "
            f"{list(non_numeric.index[:5])}..."
        )

    empty_flows = df[df[cols[0]].isna() | (df[cols[0]].astype(str).str.strip() == "")]
    if len(empty_flows) > 0:
        raise ValidationError(
            f"Empty flow names at rows: {list(empty_flows.index[:5])}..."
        )

    return df


def validate_config_paths(config: dict) -> list[str]:
    """Check that all file paths in a config exist. Returns list of warnings."""
    warnings = []
    files_section = config.get("files", {})

    for key in ("excel", "reference_zip", "model_zip"):
        val = files_section.get(key)
        if val and not Path(val).exists():
            if key == "reference_zip":
                warnings.append(f"Reference ZIP not found: {val} (will generate new IDs)")
            elif key == "model_zip":
                warnings.append(f"Model ZIP not found: {val} (will create structure from scratch)")
            else:
                raise ValidationError(f"Required file not found: {val} (key: files.{key})")

    return warnings


def print_validation_report(df: pd.DataFrame) -> None:
    """Print a summary of the loaded Excel data."""
    flow_col, cat_col, factor_col, unit_col, loc_col = (
        "Flow", "Category", "Factor", "Unit", "Location"
    )

    print(f"  Rows:        {len(df)}")
    print(f"  Flows:       {df[flow_col].nunique()} unique substances")
    print(f"  Categories:  {df[cat_col].nunique()} compartments")
    print(f"  Locations:   {df[loc_col].nunique()} regions")
    print(f"  Unit:        {df[unit_col].iloc[0] if len(df) > 0 else 'N/A'}")
    print(f"  Factor range: {df[factor_col].min():.6e} to {df[factor_col].max():.6e}")
