"""
Data models for OpenLCA JSON-LD entities.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


def new_uuid() -> str:
    return str(uuid.uuid4())


@dataclass
class UnitDef:
    name: str
    uid: str = field(default_factory=new_uuid)


@dataclass
class UnitGroupDef:
    name: str
    unit: UnitDef
    category: str = "Technical unit groups"
    uid: str = field(default_factory=new_uuid)

    def to_dict(self) -> dict:
        return {
            "@type": "UnitGroup",
            "@id": self.uid,
            "name": self.name,
            "category": self.category,
            "default": True,
            "units": [
                {
                    "@type": "Unit",
                    "@id": self.unit.uid,
                    "name": self.unit.name,
                    "factor": 1.0,
                    "isReferenceUnit": True,
                }
            ],
        }


@dataclass
class FlowPropertyDef:
    name: str
    unit_group: UnitGroupDef
    category: str = "Technical flow properties"
    flow_property_type: str = "PHYSICAL_QUANTITY"
    uid: str = field(default_factory=new_uuid)

    def to_dict(self) -> dict:
        return {
            "@type": "FlowProperty",
            "@id": self.uid,
            "name": self.name,
            "category": self.category,
            "flowPropertyType": self.flow_property_type,
            "unitGroup": {
                "@type": "UnitGroup",
                "@id": self.unit_group.uid,
                "name": self.unit_group.name,
                "category": self.unit_group.category,
            },
        }


@dataclass
class FlowDef:
    name: str
    category: str
    flow_property: FlowPropertyDef
    uid: str = field(default_factory=new_uuid)

    def to_dict(self) -> dict:
        return {
            "@type": "Flow",
            "@id": self.uid,
            "name": self.name,
            "description": None,
            "category": self.category,
            "version": "00.00.000",
            "flowType": "ELEMENTARY_FLOW",
            "casNumber": None,
            "synonyms": [],
            "isInfrastructureFlow": False,
            "flowProperties": [
                {
                    "@type": "FlowPropertyFactor",
                    "isRefFlowProperty": True,
                    "conversionFactor": 1.0,
                    "flowProperty": {
                        "@type": "FlowProperty",
                        "@id": self.flow_property.uid,
                        "name": self.flow_property.name,
                        "refUnit": self.flow_property.unit_group.unit.name,
                        "category": self.flow_property.category,
                    },
                }
            ],
            "conversionFactor": 1.0,
            "location": None,
        }


@dataclass
class ImpactFactorDef:
    value: float
    flow: FlowDef
    input_unit: UnitDef
    input_flow_property: FlowPropertyDef

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "flow": {
                "@type": "Flow",
                "@id": self.flow.uid,
                "name": self.flow.name,
                "category": self.flow.category,
                "flowType": "ELEMENTARY_FLOW",
                "refUnit": self.input_flow_property.unit_group.unit.name,
            },
            "unit": {
                "@type": "Unit",
                "@id": self.input_unit.uid,
                "name": self.input_unit.name,
            },
            "flowProperty": {
                "@type": "FlowProperty",
                "@id": self.input_flow_property.uid,
                "category": self.input_flow_property.category,
                "name": self.input_flow_property.name,
                "refUnit": self.input_flow_property.unit_group.unit.name,
                "isRefFlowProperty": True,
            },
        }


@dataclass
class ImpactCategoryDef:
    name: str
    description: str
    ref_unit: str
    method_category: str = "endpoint"
    uid: str = field(default_factory=new_uuid)
    impact_factors: list[ImpactFactorDef] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "@type": "ImpactCategory",
            "@id": self.uid,
            "name": self.name,
            "description": self.description,
            "refUnit": self.ref_unit,
            "category": self.method_category,
            "impactFactors": [f.to_dict() for f in self.impact_factors],
        }


@dataclass
class ImpactMethodDef:
    name: str
    description: str
    categories: list[ImpactCategoryDef] = field(default_factory=list)
    version: str = "1.0"
    uid: str = field(default_factory=new_uuid)

    def to_dict(self) -> dict:
        return {
            "@type": "ImpactMethod",
            "@id": self.uid,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "impactCategories": [
                {
                    "@type": "ImpactCategory",
                    "@id": cat.uid,
                    "name": cat.name,
                    "category": cat.method_category,
                    "refUnit": cat.ref_unit,
                }
                for cat in self.categories
            ],
        }


@dataclass
class MethodConfig:
    """Parsed representation of a YAML config file."""

    method_name: str
    method_description: str
    category_name: str
    category_description: str
    category_type: str  # endpoint | midpoint
    input_unit_name: str
    input_property_name: str
    output_unit_name: str
    output_property_name: str
    excel_path: str
    reference_zip: Optional[str]
    model_zip: Optional[str]
    output_zip: str
    excel_columns: dict = field(default_factory=lambda: {
        "flow": "Flow",
        "category": "Category",
        "factor": "Factor",
        "unit": "Unit",
        "location": "Location",
    })
