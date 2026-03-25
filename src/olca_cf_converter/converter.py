"""
Core conversion engine: Excel → OpenLCA JSON-LD ZIP package.

This module is the heart of olca-cf-converter. It reads characterization factors
from a spreadsheet and produces a complete OpenLCA-importable ZIP containing:
  - Unit definitions (input + output)
  - Unit groups
  - Flow properties
  - Elementary flows (reusing Ecoinvent IDs when available)
  - LCIA impact category with all characterization factors
  - LCIA method referencing the category
  - openlca.json manifest (schema version 2)
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path

import pandas as pd

from .schemas import (
    FlowDef,
    FlowPropertyDef,
    ImpactCategoryDef,
    ImpactFactorDef,
    ImpactMethodDef,
    MethodConfig,
    UnitDef,
    UnitGroupDef,
    new_uuid,
)
from .validator import validate_excel


def _write_json(directory: Path, uid: str, data: dict) -> None:
    """Write a JSON file named {uid}.json inside directory."""
    path = directory / f"{uid}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_reference_flows(ref_zip: str | Path | None) -> dict[tuple[str, str], str]:
    """Load existing flow IDs from a reference ZIP (e.g., Ecoinvent export).

    Returns a dict mapping (flow_name, category) -> existing UUID.
    """
    if ref_zip is None:
        return {}

    ref_zip = Path(ref_zip)
    if not ref_zip.exists():
        print(f"  ⚠ Reference ZIP not found: {ref_zip}. Generating new IDs.")
        return {}

    existing: dict[tuple[str, str], str] = {}
    ref_dir = Path(f"_ref_temp_{os.getpid()}")

    try:
        if ref_zip.is_dir():
            flows_dir = ref_zip / "flows"
        else:
            shutil.rmtree(ref_dir, ignore_errors=True)
            ref_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(ref_zip, "r") as zf:
                zf.extractall(ref_dir)
            flows_dir = ref_dir / "flows"

        if not flows_dir.is_dir():
            print(f"  ⚠ No 'flows/' folder in reference. Generating new IDs.")
            return {}

        for fn in flows_dir.iterdir():
            if fn.suffix != ".json":
                continue
            try:
                with open(fn, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("@type") == "Flow":
                    name = data.get("name")
                    cat = data.get("category")
                    fid = data.get("@id")
                    if name and cat and fid:
                        existing.setdefault((name, cat), fid)
            except Exception:
                continue

        print(f"  ✓ Loaded {len(existing)} reference flow IDs")
    finally:
        if ref_dir.exists() and not ref_zip.is_dir():
            shutil.rmtree(ref_dir, ignore_errors=True)

    return existing


def _extract_model_base(model_zip: str | Path | None, temp_dir: Path) -> None:
    """Extract model ZIP as the base structure, or create minimal structure."""
    if model_zip is None:
        return

    model_zip = Path(model_zip)
    if not model_zip.exists():
        print(f"  ⚠ Model ZIP not found: {model_zip}. Creating structure from scratch.")
        return

    if model_zip.is_dir():
        # Copy directory contents
        for item in model_zip.iterdir():
            dest = temp_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
    else:
        with zipfile.ZipFile(model_zip, "r") as zf:
            zf.extractall(temp_dir)

    print(f"  ✓ Base structure loaded from model")


def convert(config: MethodConfig) -> Path:
    """Execute the full conversion pipeline.

    Args:
        config: A MethodConfig with all parameters.

    Returns:
        Path to the generated ZIP file.
    """
    output_path = Path(config.output_zip)
    temp_dir = Path(f"_olca_build_{os.getpid()}")

    try:
        # Clean slate
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(exist_ok=True)

        # Step 1: Extract model base (optional)
        _extract_model_base(config.model_zip, temp_dir)

        # Step 2: Load reference flows for ID reuse (optional)
        existing_flows = _load_reference_flows(config.reference_zip)

        # Step 3: Read and validate Excel
        col = config.excel_columns
        df = validate_excel(
            config.excel_path,
            required_columns=[col["flow"], col["category"], col["factor"], col["unit"], col["location"]],
        )
        print(f"  ✓ Loaded {len(df)} characterization factors from Excel")

        # Step 4: Create input units (what goes INTO the environment, e.g., kg)
        input_unit = UnitDef(name=config.input_unit_name)
        input_unit_group = UnitGroupDef(
            name=f"{config.input_property_name} units",
            unit=input_unit,
        )
        input_flow_property = FlowPropertyDef(
            name=config.input_property_name,
            unit_group=input_unit_group,
        )

        # Step 5: Create output units (the impact, e.g., DALY, kg CO2-eq)
        output_unit = UnitDef(name=config.output_unit_name)
        output_unit_group = UnitGroupDef(
            name=f"{config.output_property_name} units",
            unit=output_unit,
            category="Impact category indicators" if config.category_type == "endpoint" else "Technical unit groups",
        )
        output_flow_property = FlowPropertyDef(
            name=config.output_property_name,
            unit_group=output_unit_group,
            category="Impact category indicators" if config.category_type == "endpoint" else "Technical flow properties",
        )

        # Step 6: Write unit/group/property files
        dirs = {
            "units": temp_dir / "units",
            "unit_groups": temp_dir / "unit_groups",
            "flow_properties": temp_dir / "flow_properties",
            "flows": temp_dir / "flows",
            "lcia_categories": temp_dir / "lcia_categories",
            "lcia_methods": temp_dir / "lcia_methods",
        }
        for d in dirs.values():
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)

        # Units
        _write_json(dirs["units"], input_unit.uid, {
            "@type": "Unit", "@id": input_unit.uid,
            "name": input_unit.name, "referenceUnitName": input_unit.name,
            "synonyms": [], "internalId": None, "default": True,
        })
        _write_json(dirs["units"], output_unit.uid, {
            "@type": "Unit", "@id": output_unit.uid,
            "name": output_unit.name, "referenceUnitName": output_unit.name,
            "synonyms": [], "internalId": None, "default": True,
        })

        # Unit groups
        _write_json(dirs["unit_groups"], input_unit_group.uid, input_unit_group.to_dict())
        _write_json(dirs["unit_groups"], output_unit_group.uid, output_unit_group.to_dict())

        # Flow properties
        _write_json(dirs["flow_properties"], input_flow_property.uid, input_flow_property.to_dict())
        _write_json(dirs["flow_properties"], output_flow_property.uid, output_flow_property.to_dict())

        # Step 7: Create flows (reusing IDs when possible)
        unique_flows = df[[col["flow"], col["category"]]].drop_duplicates()
        name_cat_to_id: dict[tuple[str, str], str] = {}

        for _, row in unique_flows.iterrows():
            flow_name = row[col["flow"]]
            category = row[col["category"]]
            key = (flow_name, category)

            flow_id = existing_flows.get(key, new_uuid())
            name_cat_to_id[key] = flow_id

            flow_def = FlowDef(
                name=flow_name,
                category=category,
                flow_property=input_flow_property,
                uid=flow_id,
            )
            _write_json(dirs["flows"], flow_id, flow_def.to_dict())

        reused = sum(1 for k in name_cat_to_id if k in existing_flows)
        created = len(name_cat_to_id) - reused
        print(f"  ✓ Flows: {reused} reused IDs + {created} new = {len(name_cat_to_id)} total")

        # Step 8: Build flow UUID map (name, category, location) -> id
        flow_uuid_map: dict[tuple[str, str, str], str] = {}
        unique_full = df[[col["flow"], col["category"], col["location"]]].drop_duplicates()
        for _, row in unique_full.iterrows():
            key_nc = (row[col["flow"]], row[col["category"]])
            fid = name_cat_to_id.get(key_nc)
            if fid:
                flow_uuid_map[(row[col["flow"]], row[col["category"]], row[col["location"]])] = fid

        # Step 9: Create impact category with all CFs
        impact_category = ImpactCategoryDef(
            name=config.category_name,
            description=config.category_description,
            ref_unit=config.output_unit_name,
            method_category=config.category_type,
        )

        skipped = 0
        for _, row in df.iterrows():
            key = (row[col["flow"]], row[col["category"]], row[col["location"]])
            flow_id = flow_uuid_map.get(key)

            if not flow_id:
                skipped += 1
                continue

            # Find the FlowDef's id
            key_nc = (row[col["flow"]], row[col["category"]])
            flow_def = FlowDef(
                name=row[col["flow"]],
                category=row[col["category"]],
                flow_property=input_flow_property,
                uid=name_cat_to_id[key_nc],
            )

            impact_category.impact_factors.append(
                ImpactFactorDef(
                    value=float(row[col["factor"]]),
                    flow=flow_def,
                    input_unit=input_unit,
                    input_flow_property=input_flow_property,
                )
            )

        if skipped > 0:
            print(f"  ⚠ Skipped {skipped} unmapped factors")

        _write_json(dirs["lcia_categories"], impact_category.uid, impact_category.to_dict())
        print(f"  ✓ Impact category: {len(impact_category.impact_factors)} factors")

        # Step 10: Create LCIA method
        method = ImpactMethodDef(
            name=config.method_name,
            description=config.method_description,
            categories=[impact_category],
        )
        _write_json(dirs["lcia_methods"], method.uid, method.to_dict())
        print(f"  ✓ Method: {config.method_name}")

        # Step 11: Write openlca.json manifest
        _write_json(temp_dir, "openlca", {"schemaVersion": 2})
        # Rename openlca.{uuid}.json -> openlca.json
        openlca_file = temp_dir / "openlca.json"
        generated = temp_dir / f"openlca.json"
        if not openlca_file.exists():
            # The _write_json wrote openlca.json already via the uid "openlca"
            # Actually we need to handle this differently
            pass
        # Fix: remove the uuid-named file and write directly
        for f in temp_dir.glob("openlca*.json"):
            f.unlink()
        with open(temp_dir / "openlca.json", "w") as f:
            json.dump({"schemaVersion": 2}, f)

        # Step 12: Package into ZIP
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    full = Path(root) / file
                    arcname = full.relative_to(temp_dir)
                    zf.write(full, arcname)

        # Count files in ZIP
        with zipfile.ZipFile(output_path, "r") as zf:
            file_count = len(zf.namelist())

        print(f"  ✓ Output: {output_path} ({file_count} files)")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output_path
