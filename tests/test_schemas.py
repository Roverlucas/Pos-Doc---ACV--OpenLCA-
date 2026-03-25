"""Tests for OpenLCA JSON-LD schema generation."""

from olca_cf_converter.schemas import (
    FlowDef,
    FlowPropertyDef,
    ImpactCategoryDef,
    ImpactFactorDef,
    ImpactMethodDef,
    UnitDef,
    UnitGroupDef,
)


def test_unit_group_to_dict():
    unit = UnitDef(name="kg", uid="u1")
    group = UnitGroupDef(name="Mass units", unit=unit, uid="g1")
    d = group.to_dict()

    assert d["@type"] == "UnitGroup"
    assert d["@id"] == "g1"
    assert d["name"] == "Mass units"
    assert len(d["units"]) == 1
    assert d["units"][0]["name"] == "kg"
    assert d["units"][0]["isReferenceUnit"] is True


def test_flow_property_to_dict():
    unit = UnitDef(name="DALY", uid="u2")
    group = UnitGroupDef(name="Impact units", unit=unit, uid="g2")
    prop = FlowPropertyDef(name="Human health", unit_group=group, uid="p1")
    d = prop.to_dict()

    assert d["@type"] == "FlowProperty"
    assert d["name"] == "Human health"
    assert d["unitGroup"]["@id"] == "g2"


def test_flow_def_to_dict():
    unit = UnitDef(name="kg", uid="u1")
    group = UnitGroupDef(name="Mass units", unit=unit, uid="g1")
    prop = FlowPropertyDef(name="Mass", unit_group=group, uid="p1")
    flow = FlowDef(name="Ammonia", category="Elementary flows/Emission to air/unspecified", flow_property=prop, uid="f1")
    d = flow.to_dict()

    assert d["@type"] == "Flow"
    assert d["name"] == "Ammonia"
    assert d["flowType"] == "ELEMENTARY_FLOW"
    assert d["flowProperties"][0]["flowProperty"]["@id"] == "p1"


def test_impact_factor_to_dict():
    unit = UnitDef(name="kg", uid="u1")
    group = UnitGroupDef(name="Mass units", unit=unit, uid="g1")
    prop = FlowPropertyDef(name="Mass", unit_group=group, uid="p1")
    flow = FlowDef(name="NOx", category="Emission to air/high pop", flow_property=prop, uid="f2")
    factor = ImpactFactorDef(value=0.00123, flow=flow, input_unit=unit, input_flow_property=prop)
    d = factor.to_dict()

    assert d["value"] == 0.00123
    assert d["flow"]["@id"] == "f2"
    assert d["unit"]["name"] == "kg"


def test_impact_category_to_dict():
    cat = ImpactCategoryDef(
        name="PM formation",
        description="Test",
        ref_unit="DALY",
        method_category="endpoint",
        uid="c1",
    )
    d = cat.to_dict()

    assert d["@type"] == "ImpactCategory"
    assert d["refUnit"] == "DALY"
    assert d["impactFactors"] == []


def test_impact_method_to_dict():
    cat = ImpactCategoryDef(name="PM", description="", ref_unit="DALY", uid="c1")
    method = ImpactMethodDef(name="My Method", description="Desc", categories=[cat], uid="m1")
    d = method.to_dict()

    assert d["@type"] == "ImpactMethod"
    assert d["name"] == "My Method"
    assert len(d["impactCategories"]) == 1
    assert d["impactCategories"][0]["@id"] == "c1"
