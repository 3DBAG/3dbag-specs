import json

from bag3d.specs.projections.cityjson import load_cityjson_projection
from bag3d.specs.projections.geopackage import load_geopackage_projection
from bag3d.specs.projections.ogc3dtiles import load_ogc3dtiles_projection
from bag3d.specs.resources import resource_file
from bag3d.specs.semantic import Attribute, AttributeType, BaseType, load_attributes
from bag3d.specs.validate_json import validate_json_file


def test_get_resource_file_path():
    """All shipped documents and schemas can be located and validated."""
    for name in (
        "semantic/attributes",
        "projections/cityjson",
        "projections/gpkg",
        "projections/ogc3dtiles",
    ):
        assert validate_json_file(
            resource_file(f"{name}.schema.json"), resource_file(f"{name}.json")
        )


def test_attribute_scalar():
    """Deserialize categorical values and optional semantic metadata."""
    data = json.loads(
        resource_file("semantic/attributes.json").read_text(encoding="utf-8")
    )
    attr = Attribute.from_dict("b3_dak_type", data["b3_dak_type"])
    assert attr.values["slanted"].en
    assert attr.items is None
    assert attr.precision is None


def test_attribute_array():
    """Array item constraints survive deserialization."""
    attr = load_attributes()["b3_val3dity_lod22"]
    assert attr.type == AttributeType(BaseType.ARRAY, BaseType.INT)
    assert str(attr.type) == "ARRAY<INT>"
    assert attr.items.type == AttributeType(BaseType.INT)
    assert attr.items.scale.en == "nominal"
    assert attr.items.nullable is False


def test_attribute_ogc3dtiles():
    """The tileset loader exposes the published physical encoding."""
    projection = load_ogc3dtiles_projection()
    for tileset in projection.tilesets:
        prop = tileset.properties["b3_val3dity_lod22"]
        assert prop.component_type == "STRING"
        assert prop.encoding == "json"


def test_load_from_package():
    """Load semantic definitions and the two other native projections."""
    assert load_attributes()["identificatie"].nullable is False
    assert (
        load_cityjson_projection().objects["Building"]["identificatie"].type == "string"
    )
    building = next(
        c
        for c in load_geopackage_projection().containers
        if c.selector and c.selector.city_object_type == "Building"
    )
    assert building.attributes["identificatie"].column == "attributes__identificatie"
