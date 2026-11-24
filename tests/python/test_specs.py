import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from bag3d.specs.projections import geopackage
from bag3d.specs.projections.cityjson import load_cityjson_projection
from bag3d.specs.projections.geopackage import load_geopackage_projection
from bag3d.specs.projections.ogc3dtiles import load_ogc3dtiles_projection
from bag3d.specs.resources import resource_file
from bag3d.specs.semantic import Attribute, AttributeType, BaseType, load_attributes
from bag3d.specs.validate_bundle import (
    _is_strftime_format,
    validate_bundle,
    validate_bundle_file,
)
from bag3d.specs.validate_json import validate_json_file


def edit_json(
    bundle_root: Path, relative_path: str, edit: Callable[[dict[str, Any]], object]
) -> None:
    document_path = bundle_root / relative_path
    document = json.loads(document_path.read_text(encoding="utf-8"))
    edit(document)
    document_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


@pytest.fixture
def bundle_root(tmp_path: Path) -> Path:
    resource_root = Path(str(resource_file("attribute-specification.json"))).parent
    return shutil.copytree(resource_root, tmp_path / "bundle")


def test_get_resource_file_path(tmp_path):
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
    assert validate_bundle_file(resource_file("attribute-specification.json"))

    resource_root = Path(str(resource_file("attribute-specification.json"))).parent

    def bundle_with_edit(edit):
        bundle_root = tmp_path / f"bundle-{len(list(tmp_path.iterdir()))}"
        shutil.copytree(resource_root, bundle_root, dirs_exist_ok=True)
        edit(bundle_root)
        return bundle_root / "attribute-specification.json"

    for valid_format in ("%_f", "%-q", "%0s", "%_u", "%#z", "%d %b %Y"):
        assert _is_strftime_format(valid_format)
    for invalid_format in (
        "%.7f",
        "%99Y",
        "%^Y",
        "%::::z",
        "%EY",
        "%_3f",
        "%^A",
        "%#A",
    ):
        with pytest.raises(ValueError, match="Chrono/strftime"):
            validate_bundle(
                bundle_with_edit(
                    lambda bundle_root, value=invalid_format: edit_json(
                        bundle_root,
                        "semantic/attributes.json",
                        lambda data: data["eindregistratie"].update(valueFormat=value),
                    )
                )
            )
    with pytest.raises(ValueError, match="encoding"):
        validate_bundle(
            bundle_with_edit(
                lambda bundle_root: edit_json(
                    bundle_root,
                    "projections/ogc3dtiles.json",
                    lambda data: data["tilesets"][0]["properties"][
                        "identificatie"
                    ].update(encoding="boolean-integer"),
                )
            )
        )
    with pytest.raises(ValueError, match="incompatible array"):
        validate_bundle(
            bundle_with_edit(
                lambda bundle_root: edit_json(
                    bundle_root,
                    "projections/ogc3dtiles.json",
                    lambda data: data["tilesets"][2]["properties"][
                        "b3_val3dity_lod22"
                    ].update(encoding="json"),
                )
            )
        )
    with pytest.raises(ValueError, match="duplicate selector"):
        validate_bundle(
            bundle_with_edit(
                lambda bundle_root: edit_json(
                    bundle_root,
                    "projections/ogc3dtiles.json",
                    lambda data: data["tilesets"][2]["selector"].update(
                        lod=data["tilesets"][0]["selector"]["lod"]
                    ),
                )
            )
        )
    with pytest.raises(ValueError, match="structural column"):
        validate_bundle(
            bundle_with_edit(
                lambda bundle_root: edit_json(
                    bundle_root,
                    "projections/gpkg.json",
                    lambda data: data["containers"][0]["structuralColumns"].append(
                        "ATTRIBUTES__identificatie"
                    ),
                )
            )
        )
    with pytest.raises(ValueError, match="generated selector name"):
        validate_bundle(
            bundle_with_edit(
                lambda bundle_root: edit_json(
                    bundle_root,
                    "projections/gpkg.json",
                    lambda data: data["containers"][0].update(name="renamed_layer"),
                )
            )
        )


@pytest.mark.parametrize(
    ("item_type", "component"),
    [("float", "INT32"), ("int", "FLOAT32")],
)
def test_native_array_requires_compatible_component(
    bundle_root: Path, item_type: str, component: str
) -> None:
    name = "b3_val3dity_lod22"
    edit_json(
        bundle_root,
        "semantic/attributes.json",
        lambda data: data[name]["items"].update(type=item_type),
    )
    edit_json(
        bundle_root,
        "projections/ogc3dtiles.json",
        lambda data: data["tilesets"][0]["properties"][name].update(
            componentType=component
        ),
    )
    with pytest.raises(ValueError, match=f"{name}: incompatible array"):
        validate_bundle(bundle_root / "attribute-specification.json")


def test_geopackage_omitted_columns_use_attributes_prefix(
    bundle_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def omit_columns(data: dict[str, Any]) -> None:
        data["containers"][0]["attributes"]["identificatie"].pop("column")
        semantics = next(c for c in data["containers"] if c["kind"] == "semantics")
        semantics["attributes"]["b3_azimut"].pop("column")

    edit_json(bundle_root, "projections/gpkg.json", omit_columns)
    monkeypatch.setattr(
        geopackage,
        "load_resource",
        lambda path: json.loads((bundle_root / path).read_text(encoding="utf-8")),
    )

    validate_bundle(bundle_root / "attribute-specification.json")
    containers = load_geopackage_projection().containers
    assert (
        containers[0].attributes["identificatie"].column == "attributes__identificatie"
    )
    semantics = next(c for c in containers if c.kind == "semantics")
    assert semantics.attributes["b3_azimut"].column == "attributes__b3_azimut"


def test_geopackage_rejects_singular_attribute_prefix(
    bundle_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def use_singular_prefix(data: dict[str, Any]) -> None:
        semantics = next(c for c in data["containers"] if c["kind"] == "semantics")
        semantics["attributes"]["b3_azimut"]["column"] = "attribute__b3_azimut"

    edit_json(bundle_root, "projections/gpkg.json", use_singular_prefix)
    monkeypatch.setattr(
        geopackage,
        "load_resource",
        lambda path: json.loads((bundle_root / path).read_text(encoding="utf-8")),
    )

    with pytest.raises(jsonschema.ValidationError, match="attributes__"):
        validate_bundle(bundle_root / "attribute-specification.json")
    with pytest.raises(ValueError, match="expected column 'attributes__b3_azimut'"):
        load_geopackage_projection()


@pytest.mark.parametrize(
    ("component", "sentinel", "valid"),
    [
        ("FLOAT32", 1e100, False),
        ("FLOAT32", -1e100, False),
        ("FLOAT32", -3.4028234663852886e38, True),
        ("FLOAT64", 1e100, True),
        ("FLOAT64", 10**400, False),
    ],
)
def test_float_sentinel_fits_component(
    bundle_root: Path, component: str, sentinel: float, valid: bool
) -> None:
    edit_json(
        bundle_root,
        "projections/ogc3dtiles.json",
        lambda data: data["tilesets"][0]["properties"]["b3_h_maaiveld"].update(
            componentType=component, noData=sentinel
        ),
    )
    manifest = bundle_root / "attribute-specification.json"
    if valid:
        validate_bundle(manifest)
    else:
        with pytest.raises(ValueError, match=f"noData is outside {component} storage"):
            validate_bundle(manifest)


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
    assert attr.type == AttributeType(BaseType.ARRAY, AttributeType(BaseType.INT))
    assert str(attr.type) == "ARRAY<INT>"
    assert attr.items.type == AttributeType(BaseType.INT)
    assert attr.items.scale.en == "nominal"
    assert attr.items.nullable is False

    nested_definition = {
        "type": "array",
        "semanticType": "nested values",
        "nullable": False,
        "items": {
            "type": "array",
            "description": {"nl": "waarden", "en": "values"},
            "semanticType": "values",
            "nullable": True,
            "items": {
                "type": "int",
                "description": {"nl": "waarde", "en": "value"},
                "semanticType": "value",
                "nullable": False,
            },
        },
        "description": {"nl": "geneste waarden", "en": "nested values"},
        "source": "test fixture",
    }
    nested = Attribute.from_dict("nested_values", nested_definition)
    assert str(nested.type) == "ARRAY<ARRAY<INT>>"
    assert nested.items.items.nullable is False


def test_attribute_ogc3dtiles():
    """The tileset loader exposes the published physical encoding."""
    projection = load_ogc3dtiles_projection()
    for tileset in projection.tilesets:
        prop = tileset.properties["b3_val3dity_lod22"]
        assert prop.component_type == "INT32"
        assert prop.shape == "array"
        assert prop.encoding is None


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
