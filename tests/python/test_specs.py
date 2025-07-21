from bag3d.specs.resources import get_resource_file_path
from bag3d.specs.core import (
    Attribute,
    AttributeType,
    load_attributes_spec,
    BaseType,
    CityJSONLocation,
)


def test_get_resource_file_path():
    """Can we get the path of a resource file?"""
    assert get_resource_file_path("attributes.json").is_file()


def test_attribute_scalar():
    """Can we deserialize an attribute with all of its values?"""
    data = {
        "type": "string",
        "source": "source",
        "nullable": "true",
        "appliesTo": {},
        "precision": 2,
        "unit": {"en": "metre", "nl": "meter"},
        "valueFormat": "YYYY",
        "semanticType": "category",
        "values": {"yes": {"nl": "Ja", "en": "Yes"}, "no": {"nl": "Nee", "en": "No"}},
        "description": {"nl": "Test", "en": "Test"},
        "scale": {"en": "ratio", "nl": "ratio"},
    }

    attr = Attribute.from_dict("test_bool", data)

    assert attr.values is not None
    assert len(attr.values) == 2
    assert attr.values["yes"].en == "Yes"
    assert attr.values["no"].nl == "Nee"


def test_attribute_array():
    """Can we deserialize an array attribute?"""
    data = {
        "type": "array",
        "source": "source",
        "nullable": True,
        "appliesTo": {
            "cityjson": {"locations": ["RoofSurface"]},
            "gpkg": {"locations": ["lod22_2d"]},
        },
        "precision": 2,
        "unit": {"en": "metre", "nl": "meter"},
        "valueFormat": "YYYY",
        "semanticType": "category",
        "values": {"yes": {"nl": "Ja", "en": "Yes"}, "no": {"nl": "Nee", "en": "No"}},
        "description": {"nl": "Test", "en": "Test"},
        "scale": None,
        "items": {
            "type": "int",
            "semanticType": "category",
            "description": {"nl": "Test", "en": "Test"},
            "scale": {"en": "ratio", "nl": "ratio"},
        },
    }

    attr = Attribute.from_dict("test_bool", data)

    assert attr.type == AttributeType(BaseType.ARRAY, BaseType.INT)
    assert str(attr.type) == "ARRAY<INT>"
    assert attr.items.scale.en == "ratio"
    assert CityJSONLocation.RoofSurface in attr.applies_to.cityjson["locations"]


def test_load_from_package():
    """Can we load the attribute specs from the package?"""
    attributes_spec = load_attributes_spec()
    assert "identificatie" in attributes_spec
