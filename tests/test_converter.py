"""Tests for the core conversion engine."""

import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from olca_cf_converter.converter import convert
from olca_cf_converter.schemas import MethodConfig


@pytest.fixture
def sample_excel(tmp_path):
    """Create a sample CF Excel file."""
    df = pd.DataFrame({
        "Flow": [
            "Ammonia", "Ammonia", "Ammonia",
            "Nitrogen oxides", "Nitrogen oxides",
            "Sulfur dioxide",
        ],
        "Category": [
            "Elementary flows/Emission to air/unspecified",
            "Elementary flows/Emission to air/unspecified",
            "Elementary flows/Emission to air/high population density",
            "Elementary flows/Emission to air/unspecified",
            "Elementary flows/Emission to air/high population density",
            "Elementary flows/Emission to air/unspecified",
        ],
        "Factor": [0.00058, 0.00032, 0.00058, 0.00123, 0.00145, 0.00045],
        "Unit": ["DALY"] * 6,
        "Location": ["Brazil", "Brazil, SP", "Brazil", "Brazil", "Brazil", "Brazil"],
    })
    path = tmp_path / "test-cfs.xlsx"
    df.to_excel(path, index=False)
    return path


@pytest.fixture
def basic_config(sample_excel, tmp_path):
    """Create a minimal MethodConfig."""
    return MethodConfig(
        method_name="Test Method",
        method_description="A test method for unit tests.",
        category_name="test impact",
        category_description="Test description",
        category_type="endpoint",
        input_unit_name="kg",
        input_property_name="Mass",
        output_unit_name="DALY",
        output_property_name="Impact on human health",
        excel_path=str(sample_excel),
        reference_zip=None,
        model_zip=None,
        output_zip=str(tmp_path / "output.zip"),
    )


def test_convert_produces_zip(basic_config):
    result = convert(basic_config)
    assert result.exists()
    assert result.suffix == ".zip"


def test_zip_contains_required_structure(basic_config):
    result = convert(basic_config)

    with zipfile.ZipFile(result, "r") as zf:
        names = zf.namelist()

    # Check required directories exist
    assert any(n.startswith("flows/") for n in names)
    assert any(n.startswith("units/") for n in names)
    assert any(n.startswith("unit_groups/") for n in names)
    assert any(n.startswith("flow_properties/") for n in names)
    assert any(n.startswith("lcia_categories/") for n in names)
    assert any(n.startswith("lcia_methods/") for n in names)
    assert "openlca.json" in names


def test_flows_have_correct_structure(basic_config):
    result = convert(basic_config)

    with zipfile.ZipFile(result, "r") as zf:
        flow_files = [n for n in zf.namelist() if n.startswith("flows/") and n.endswith(".json")]

        for ff in flow_files:
            data = json.loads(zf.read(ff))
            assert data["@type"] == "Flow"
            assert data["flowType"] == "ELEMENTARY_FLOW"
            assert "@id" in data
            assert "name" in data
            assert len(data["flowProperties"]) > 0


def test_impact_factors_count(basic_config):
    result = convert(basic_config)

    with zipfile.ZipFile(result, "r") as zf:
        cat_files = [n for n in zf.namelist() if n.startswith("lcia_categories/")]
        assert len(cat_files) == 1

        data = json.loads(zf.read(cat_files[0]))
        assert len(data["impactFactors"]) == 6


def test_method_references_category(basic_config):
    result = convert(basic_config)

    with zipfile.ZipFile(result, "r") as zf:
        method_files = [n for n in zf.namelist() if n.startswith("lcia_methods/")]
        cat_files = [n for n in zf.namelist() if n.startswith("lcia_categories/")]

        method = json.loads(zf.read(method_files[0]))
        category = json.loads(zf.read(cat_files[0]))

        assert method["impactCategories"][0]["@id"] == category["@id"]


def test_unique_flows_deduplication(basic_config):
    """Ammonia appears in 2 categories → 2 flow files (not 3)."""
    result = convert(basic_config)

    with zipfile.ZipFile(result, "r") as zf:
        flow_files = [n for n in zf.namelist() if n.startswith("flows/") and n.endswith(".json")]
        # 3 unique (name, category) combos: Ammonia/unspec, Ammonia/high-pop, NOx/unspec, NOx/high-pop, SO2/unspec
        assert len(flow_files) == 5


def test_midpoint_config(sample_excel, tmp_path):
    """Test with midpoint category type and different units."""
    config = MethodConfig(
        method_name="GWP Test",
        method_description="Test GWP",
        category_name="climate change",
        category_description="GWP100",
        category_type="midpoint",
        input_unit_name="kg",
        input_property_name="Mass",
        output_unit_name="kg CO2-Eq",
        output_property_name="Global warming potential",
        excel_path=str(sample_excel),
        reference_zip=None,
        model_zip=None,
        output_zip=str(tmp_path / "gwp-output.zip"),
    )
    result = convert(config)
    assert result.exists()

    with zipfile.ZipFile(result, "r") as zf:
        cat_files = [n for n in zf.namelist() if n.startswith("lcia_categories/")]
        data = json.loads(zf.read(cat_files[0]))
        assert data["refUnit"] == "kg CO2-Eq"
        assert data["category"] == "midpoint"


def test_reference_zip_id_reuse(sample_excel, tmp_path):
    """Test that flow IDs from a reference ZIP are reused."""
    # Create a fake reference ZIP with one matching flow
    ref_dir = tmp_path / "ref"
    flows_dir = ref_dir / "flows"
    flows_dir.mkdir(parents=True)

    known_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    flow_data = {
        "@type": "Flow",
        "@id": known_id,
        "name": "Ammonia",
        "category": "Elementary flows/Emission to air/unspecified",
    }
    with open(flows_dir / f"{known_id}.json", "w") as f:
        json.dump(flow_data, f)

    ref_zip = tmp_path / "ref.zip"
    with zipfile.ZipFile(ref_zip, "w") as zf:
        for p in flows_dir.iterdir():
            zf.write(p, f"flows/{p.name}")

    config = MethodConfig(
        method_name="Reuse Test",
        method_description="Test ID reuse",
        category_name="test",
        category_description="test",
        category_type="endpoint",
        input_unit_name="kg",
        input_property_name="Mass",
        output_unit_name="DALY",
        output_property_name="Impact",
        excel_path=str(sample_excel),
        reference_zip=str(ref_zip),
        model_zip=None,
        output_zip=str(tmp_path / "reuse-output.zip"),
    )
    result = convert(config)

    with zipfile.ZipFile(result, "r") as zf:
        flow_files = [n for n in zf.namelist() if n.startswith("flows/")]
        # The known ID should appear as a filename
        assert f"flows/{known_id}.json" in flow_files
