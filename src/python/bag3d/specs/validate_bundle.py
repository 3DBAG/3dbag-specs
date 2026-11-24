"""Validate a complete manifest-linked semantic and projection bundle."""

import argparse
import math
import re
from pathlib import Path
from sys import float_info
from typing import Any
from urllib.parse import unquote, urlsplit

import jsonschema
from bag3d.specs.projections.geopackage import attribute_column_name
from bag3d.specs.validate_json import read_json, validate_semantic_rules

CONTRACT_VERSION = "1.0"
PROJECTIONS = {"cityjson", "gpkg", "ogc3dtiles"}
INTEGER_COMPONENTS = {
    "INT8": (-(2**7), 2**7 - 1),
    "UINT8": (0, 2**8 - 1),
    "INT16": (-(2**15), 2**15 - 1),
    "UINT16": (0, 2**16 - 1),
    "INT32": (-(2**31), 2**31 - 1),
    "UINT32": (0, 2**32 - 1),
    "INT64": (-(2**63), 2**63 - 1),
    "UINT64": (0, 2**64 - 1),
}
FLOAT_COMPONENTS: dict[str, float] = {
    "FLOAT32": float.fromhex("0x1.fffffep+127"),
    "FLOAT64": float_info.max,
}
TEMPORAL_DIRECTIVES = set("AaBCcDdefFfGgHhIjklMmnpPRrSsTtUuVvWwXxYyZz+b%q")
PAD_DIRECTIVES = set("CYymdeHkIlMSfUWVjGgsquw")


def _validate_schema(schema_path: Path, document_path: Path) -> dict[str, Any]:
    schema = read_json(schema_path)
    data = read_json(document_path)
    jsonschema.validate(data, schema)
    return data


def _is_strftime_format(value: str) -> bool:
    """Check Chrono/strftime directives without requiring a complete date."""
    index = 0
    while index < len(value):
        if value[index] != "%":
            index += 1
            continue
        index += 1
        if index == len(value):
            return False
        if value[index] == ".":
            index += 1
            digits_start = index
            while index < len(value) and value[index].isdigit():
                index += 1
            precision = value[digits_start:index]
            if (
                index >= len(value)
                or value[index] != "f"
                or precision not in {"", "3", "6", "9"}
            ):
                return False
            index += 1
            continue
        if value[index] == ":":
            colon_count = 0
            while index < len(value) and value[index] == ":":
                colon_count += 1
                index += 1
            if index >= len(value) or value[index] != "z" or colon_count > 3:
                return False
            index += 1
            continue
        modifier = ""
        if index < len(value) and value[index] in "-_0#":
            modifier = value[index]
            index += 1
            if index < len(value) and value[index] in "-_0#":
                return False
        digits_start = index
        while index < len(value) and value[index].isdigit():
            index += 1
        width = value[digits_start:index]
        if index >= len(value) or value[index] not in TEMPORAL_DIRECTIVES:
            return False
        directive = value[index]
        if width and (directive != "f" or width not in {"3", "6", "9"}):
            return False
        if modifier and width:
            return False
        if modifier in "-_0" and modifier and directive not in PAD_DIRECTIVES:
            return False
        if modifier == "#" and directive != "z":
            return False
        index += 1
    return True


def _parse_category_key(key: str, value_type: str) -> str | int | float | bool:
    if value_type == "string":
        return key
    if value_type == "bool":
        lowered = key.lower()
        if lowered not in {"true", "false"}:
            raise ValueError(f"categorical boolean key {key!r} is not true or false")
        return lowered == "true"
    if value_type == "int":
        if re.fullmatch(r"[+-]?(?:0|[1-9][0-9]*)", key) is None:
            raise ValueError(f"categorical integer key {key!r} is invalid")
        return int(key)
    if value_type == "float":
        try:
            parsed = float(key)
        except ValueError as exc:
            raise ValueError(f"categorical float key {key!r} is invalid") from exc
        if not math.isfinite(parsed):
            raise ValueError(f"categorical float key {key!r} must be finite")
        return parsed
    if value_type in {"date", "datetime"}:
        return key
    raise ValueError(f"categorical keys are unsupported for {value_type}")


def _validate_semantics(semantic: dict[str, Any]) -> None:
    validate_semantic_rules(semantic)
    for name, attribute in semantic.items():

        def validate_value(value: dict[str, Any], label: str) -> None:
            value_type = value["type"]
            value_format = value.get("valueFormat")
            if value_type in {"date", "datetime"}:
                if not isinstance(value_format, str) or not value_format:
                    raise ValueError(
                        f"{label}: temporal values require a non-empty valueFormat"
                    )
                if not _is_strftime_format(value_format):
                    raise ValueError(
                        f"{label}: invalid Chrono/strftime valueFormat {value_format!r}"
                    )
            if "values" in value:
                parsed = [
                    _parse_category_key(key, value_type) for key in value["values"]
                ]
                if len(parsed) != len(set(parsed)):
                    raise ValueError(
                        f"{label}: categorical keys are not unique after parsing"
                    )
            if "items" in value:
                validate_value(value["items"], f"{label}.items")

        validate_value(attribute, name)


def _compatible_cityjson(
    name: str, entry: dict[str, Any], semantic: dict[str, Any]
) -> None:
    value_type = semantic[name]["type"]
    expected = {
        "int": "number",
        "float": "number",
        "bool": "boolean",
        "string": "string",
        "date": "string",
        "datetime": "string",
        "array": "array",
    }[value_type]
    if entry["type"] != expected or "encoding" in entry:
        raise ValueError(
            f"cityjson {name}: incompatible type or encoding for semantic {value_type}"
        )
    if entry.get("property", name) != name:
        raise ValueError(f"cityjson {name}: attribute renaming is not supported")


def _compatible_gpkg(
    name: str, entry: dict[str, Any], semantic: dict[str, Any]
) -> None:
    value_type = semantic[name]["type"]
    expected = {
        "int": ("INTEGER",),
        "float": ("REAL",),
        "bool": ("BOOLEAN", "INTEGER"),
        "string": ("TEXT",),
        "date": ("TEXT",),
        "datetime": ("TEXT",),
        "array": ("TEXT",),
    }[value_type]
    if entry["type"] not in expected:
        raise ValueError(
            f"gpkg {name}: expected {' or '.join(expected)} storage "
            f"for semantic {value_type}"
        )
    if value_type == "array":
        if entry.get("encoding") != "json":
            raise ValueError(f"gpkg {name}: arrays require JSON text encoding")
    elif "encoding" in entry:
        raise ValueError(f"gpkg {name}: encoding is only supported for arrays")


def _compatible_tiles(
    name: str, entry: dict[str, Any], semantic: dict[str, Any]
) -> None:
    value = semantic[name]
    value_type = value["type"]
    component = entry["componentType"]
    shape = entry.get("shape", "scalar")
    encoding = entry.get("encoding")
    if entry.get("property", name) != name:
        raise ValueError(f"ogc3dtiles {name}: attribute renaming is not supported")
    if value_type == "array":
        item_type = value["items"]["type"]
        native = shape == "array" and (
            (
                (
                    (item_type == "int" and component in INTEGER_COMPONENTS)
                    or (item_type == "float" and component in FLOAT_COMPONENTS)
                )
                and encoding is None
            )
            or (
                item_type == "bool"
                and (
                    (component == "BOOLEAN" and encoding is None)
                    or (
                        component in INTEGER_COMPONENTS
                        and encoding == "boolean-integer"
                    )
                )
            )
            or (
                item_type in {"string", "date", "datetime"}
                and component == "STRING"
                and encoding is None
            )
        )
        json_text = shape == "scalar" and component == "STRING" and encoding == "json"
        if not native and not json_text:
            raise ValueError(
                f"ogc3dtiles {name}: incompatible array shape or component type"
            )
        if shape == "array" and "noData" in entry:
            raise ValueError(
                f"ogc3dtiles {name}: array properties cannot declare scalar noData"
            )
        if json_text and "nullEncoding" in entry:
            raise ValueError(
                f"ogc3dtiles {name}: JSON text arrays cannot use nullEncoding"
            )
    elif shape != "scalar":
        raise ValueError(
            f"ogc3dtiles {name}: scalar semantic values require scalar shape"
        )
    elif value_type == "int" and component not in INTEGER_COMPONENTS:
        raise ValueError(
            f"ogc3dtiles {name}: integer requires integer component storage"
        )
    elif value_type == "float" and component not in FLOAT_COMPONENTS:
        raise ValueError(
            f"ogc3dtiles {name}: float requires FLOAT32 or FLOAT64 storage"
        )
    elif value_type == "bool" and not (
        component == "BOOLEAN"
        or (component in INTEGER_COMPONENTS and encoding == "boolean-integer")
    ):
        raise ValueError(
            f"ogc3dtiles {name}: boolean requires BOOLEAN or integer boolean encoding"
        )
    elif value_type in {"string", "date", "datetime"} and component != "STRING":
        raise ValueError(
            f"ogc3dtiles {name}: text semantic values require STRING storage"
        )
    if value_type != "array":
        if value_type == "bool" and component in INTEGER_COMPONENTS:
            if encoding != "boolean-integer":
                raise ValueError(
                    f"ogc3dtiles {name}: integer booleans require boolean-integer encoding"
                )
        elif encoding is not None:
            raise ValueError(
                f"ogc3dtiles {name}: encoding is not supported for this scalar value"
            )
    no_data = entry.get("noData")
    if "noData" in entry:
        if component in INTEGER_COMPONENTS:
            bounds = INTEGER_COMPONENTS[component]
            if (
                isinstance(no_data, bool)
                or not isinstance(no_data, int)
                or not bounds[0] <= no_data <= bounds[1]
            ):
                raise ValueError(
                    f"ogc3dtiles {name}: noData is outside {component} storage"
                )
        elif component in FLOAT_COMPONENTS:
            limit = FLOAT_COMPONENTS[component]
            if (
                isinstance(no_data, bool)
                or not isinstance(no_data, (float, int))
                or not -limit <= no_data <= limit
            ):
                raise ValueError(
                    f"ogc3dtiles {name}: noData is outside {component} storage"
                )
        elif component == "STRING" and not isinstance(no_data, str):
            raise ValueError(f"ogc3dtiles {name}: STRING noData must be text")
        elif component == "BOOLEAN" and not isinstance(no_data, bool):
            raise ValueError(f"ogc3dtiles {name}: BOOLEAN noData must be boolean")
    if "nullEncoding" in entry and component != "STRING":
        raise ValueError(
            f"ogc3dtiles {name}: nullEncoding is only supported for STRING"
        )


def _check_references(
    attributes: dict[str, Any], projection: dict[str, Any], format_name: str
) -> None:
    def check_map(items: dict[str, Any], path: str) -> None:
        for name in items:
            if name not in attributes:
                raise ValueError(f"{path}: {name!r} is not in the semantic catalogue")

    if format_name == "cityjson":
        for section in ("objects", "semanticSurfaces"):
            for location, container in projection.get(section, {}).items():
                check_map(container["attributes"], f"cityjson {section}.{location}")
    elif format_name == "gpkg":
        for index, container in enumerate(projection["containers"]):
            check_map(container["attributes"], f"gpkg containers[{index}]")
    else:
        for index, tileset in enumerate(projection["tilesets"]):
            check_map(tileset["properties"], f"ogc3dtiles tilesets[{index}]")


def _validate_cityjson(projection: dict[str, Any], semantic: dict[str, Any]) -> None:
    reserved = {
        "id",
        "type",
        "geometry",
        "parents",
        "children",
        "vertices",
        "transform",
        "appearance",
    }
    for section in ("objects", "semanticSurfaces"):
        for location, container in projection.get(section, {}).items():
            physical_names: set[str] = set()
            for name, entry in container["attributes"].items():
                _compatible_cityjson(name, entry, semantic)
                physical = entry.get("property", name)
                if physical in reserved:
                    raise ValueError(
                        f"cityjson {section}.{location}: {physical!r} conflicts with a structural field"
                    )
                if physical in physical_names:
                    raise ValueError(
                        f"cityjson {section}.{location}: duplicate physical property {physical!r}"
                    )
                physical_names.add(physical)


def _validate_gpkg(projection: dict[str, Any], semantic: dict[str, Any]) -> None:
    table_names = [name.casefold() for name in projection.get("structuralTables", [])]
    seen_tables = set(table_names)
    for container in projection["containers"]:
        table_name = container.get("name", container.get("table"))
        if table_name.casefold() in seen_tables:
            raise ValueError(f"gpkg: duplicate table name {table_name!r}")
        seen_tables.add(table_name.casefold())
        table_names.append(table_name.casefold())
        selector = container.get("selector")
        if selector is not None:
            expected_name = (
                f"{selector['cityObjectType']}_{selector['geometryFamily']}_lod"
                f"{selector['lod'].replace('.', '_')}"
            ).lower()
            if table_name.casefold() != expected_name.casefold():
                raise ValueError(
                    f"gpkg {table_name}: layer name must match generated selector name {expected_name!r}"
                )
        columns = {
            column.casefold() for column in container.get("structuralColumns", [])
        }
        for name, entry in container["attributes"].items():
            _compatible_gpkg(name, entry, semantic)
            column = attribute_column_name(name, entry)
            if column.casefold() in columns:
                raise ValueError(
                    f"gpkg {table_name}: duplicate or structural column {column!r}"
                )
            columns.add(column.casefold())
    if len(table_names) != len(set(table_names)):
        raise ValueError("gpkg: duplicate generated or structural table name")


def _validate_tiles(projection: dict[str, Any], semantic: dict[str, Any]) -> None:
    selectors: set[str] = set()
    for tileset in projection["tilesets"]:
        lod = tileset["selector"]["lod"]
        if lod in selectors:
            raise ValueError(f"ogc3dtiles: duplicate selector lod {lod!r}")
        selectors.add(lod)
        physical_names: set[str] = set()
        for name, entry in tileset["properties"].items():
            _compatible_tiles(name, entry, semantic)
            physical = entry.get("property", name)
            if physical in physical_names:
                raise ValueError(
                    f"ogc3dtiles {lod}: duplicate physical property {physical!r}"
                )
            physical_names.add(physical)


def validate_bundle(manifest_path: Path) -> None:
    """Validate local manifest-linked documents and their cross-file contracts."""
    manifest = _validate_schema(
        manifest_path.with_name("attribute-specification.schema.json"), manifest_path
    )
    if manifest["contractVersion"] != CONTRACT_VERSION:
        raise ValueError(
            f"unsupported contract version {manifest['contractVersion']!r}"
        )
    if set(manifest["projections"]) != PROJECTIONS:
        raise ValueError(f"manifest projections must be exactly {sorted(PROJECTIONS)}")

    documents: dict[str, dict[str, Any]] = {}
    references = {"semantic": manifest["semantic"], **manifest["projections"]}
    for kind, reference in references.items():
        parsed = urlsplit(reference)
        if (
            parsed.scheme
            or parsed.netloc
            or parsed.query
            or parsed.fragment
            or Path(unquote(parsed.path)).is_absolute()
        ):
            raise ValueError(
                f"manifest {kind} reference must be a relative local URI: {reference!r}"
            )
        relative_path = Path(unquote(parsed.path))
        if ".." in relative_path.parts:
            raise ValueError(
                f"manifest {kind} reference escapes its bundle: {reference!r}"
            )
        document_path = manifest_path.parent / relative_path
        schema_path = document_path.with_name(f"{document_path.stem}.schema.json")
        documents[kind] = _validate_schema(schema_path, document_path)

    semantic = documents["semantic"]
    _validate_semantics(semantic)
    for format_name in PROJECTIONS:
        projection = documents[format_name]
        _check_references(semantic, projection, format_name)
    _validate_cityjson(documents["cityjson"], semantic)
    _validate_gpkg(documents["gpkg"], semantic)
    _validate_tiles(documents["ogc3dtiles"], semantic)


def validate_bundle_file(manifest_path: Path) -> bool:
    """Validate one bundle and report errors at the CLI boundary."""
    try:
        validate_bundle(manifest_path)
    except (
        OSError,
        ValueError,
        jsonschema.ValidationError,
        jsonschema.SchemaError,
    ) as exc:
        print(f"{manifest_path}: {exc}")
        return False
    print(f"{manifest_path}: valid bundle")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if not validate_bundle_file(args.manifest):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
