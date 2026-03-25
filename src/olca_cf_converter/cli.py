"""
Command-line interface for olca-cf-converter.

Usage:
    olca-cf convert config.yaml       # Convert Excel → OpenLCA ZIP
    olca-cf validate data.xlsx        # Validate Excel file
    olca-cf init                      # Generate template config + Excel
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import __version__
from .converter import convert
from .schemas import MethodConfig
from .validator import (
    ValidationError,
    print_validation_report,
    validate_config_paths,
    validate_excel,
)


def _load_config(config_path: str) -> MethodConfig:
    """Parse a YAML config file into a MethodConfig."""
    path = Path(config_path)
    if not path.exists():
        print(f"✗ Config file not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Resolve paths relative to the config file's directory
    config_dir = path.parent

    files = raw.get("files", {})
    excel = files.get("excel", "")
    ref_zip = files.get("reference_zip")
    model_zip = files.get("model_zip")
    output_zip = files.get("output_zip", "output.zip")

    def resolve(p):
        if p is None:
            return None
        pp = Path(p)
        if not pp.is_absolute():
            pp = config_dir / pp
        return str(pp)

    method = raw.get("method", {})
    category = raw.get("category", {})
    units = raw.get("units", {})
    inp = units.get("input", {})
    out = units.get("output", {})

    columns = raw.get("columns", {})
    col_map = {
        "flow": columns.get("flow", "Flow"),
        "category": columns.get("category", "Category"),
        "factor": columns.get("factor", "Factor"),
        "unit": columns.get("unit", "Unit"),
        "location": columns.get("location", "Location"),
    }

    return MethodConfig(
        method_name=method.get("name", "Unnamed Method"),
        method_description=method.get("description", ""),
        category_name=category.get("name", "Unnamed Category"),
        category_description=category.get("description", ""),
        category_type=category.get("type", "endpoint"),
        input_unit_name=inp.get("name", "kg"),
        input_property_name=inp.get("property", "Mass"),
        output_unit_name=out.get("name", "DALY"),
        output_property_name=out.get("property", "Impact on human health"),
        excel_path=resolve(excel),
        reference_zip=resolve(ref_zip),
        model_zip=resolve(model_zip),
        output_zip=resolve(output_zip),
        excel_columns=col_map,
    )


def cmd_convert(args: argparse.Namespace) -> None:
    """Execute the conversion pipeline."""
    print(f"{'='*60}")
    print(f"  olca-cf-converter v{__version__}")
    print(f"{'='*60}")
    print()

    config = _load_config(args.config)

    print(f"  Method:   {config.method_name}")
    print(f"  Category: {config.category_name}")
    print(f"  Units:    {config.input_unit_name} → {config.output_unit_name}")
    print(f"  Excel:    {config.excel_path}")
    print()

    # Validate paths
    with open(args.config, "r") as f:
        raw = yaml.safe_load(f)
    warnings = validate_config_paths(raw)
    for w in warnings:
        print(f"  ⚠ {w}")

    print("  Converting...")
    print()

    try:
        output = convert(config)
        print()
        print(f"  ✅ Done! Import this file into OpenLCA:")
        print(f"     {output}")
        print()
        print(f"  OpenLCA: File → Import → JSON-LD → select the ZIP")
    except ValidationError as e:
        print(f"\n  ✗ Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ✗ Conversion failed: {e}")
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate an Excel file."""
    print(f"  Validating: {args.excel}")
    print()

    try:
        df = validate_excel(args.excel)
        print_validation_report(df)
        print()
        print("  ✅ Excel file is valid!")
    except ValidationError as e:
        print(f"  ✗ {e}")
        sys.exit(1)


def cmd_init(args: argparse.Namespace) -> None:
    """Generate a template config file."""
    template = {
        "method": {
            "name": "My LCIA Method",
            "description": "Description of the method, including citation.",
        },
        "category": {
            "name": "impact category name",
            "description": "Description of this impact category.",
            "type": "endpoint",
        },
        "units": {
            "input": {"name": "kg", "property": "Mass"},
            "output": {"name": "DALY", "property": "Impact on human health"},
        },
        "files": {
            "excel": "my-factors.xlsx",
            "reference_zip": "Base-Ecoinvent.zip",
            "model_zip": None,
            "output_zip": "My-Method-FINAL.zip",
        },
        "columns": {
            "flow": "Flow",
            "category": "Category",
            "factor": "Factor",
            "unit": "Unit",
            "location": "Location",
        },
    }

    output = Path(args.output) if args.output else Path("config.yaml")

    if output.exists() and not args.force:
        print(f"  ✗ {output} already exists. Use --force to overwrite.")
        sys.exit(1)

    with open(output, "w", encoding="utf-8") as f:
        yaml.dump(template, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"  ✅ Template config created: {output}")
    print()
    print("  Next steps:")
    print("  1. Edit the config with your method details")
    print("  2. Prepare your Excel with columns: Flow, Category, Factor, Unit, Location")
    print(f"  3. Run: olca-cf convert {output}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="olca-cf",
        description="Convert characterization factor spreadsheets into OpenLCA JSON-LD packages.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # convert
    p_convert = sub.add_parser("convert", help="Convert Excel → OpenLCA ZIP")
    p_convert.add_argument("config", help="Path to YAML config file")

    # validate
    p_validate = sub.add_parser("validate", help="Validate an Excel file")
    p_validate.add_argument("excel", help="Path to Excel file (.xlsx)")

    # init
    p_init = sub.add_parser("init", help="Generate template config file")
    p_init.add_argument("-o", "--output", help="Output path (default: config.yaml)")
    p_init.add_argument("--force", action="store_true", help="Overwrite if exists")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "convert": cmd_convert,
        "validate": cmd_validate,
        "init": cmd_init,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
