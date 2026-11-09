"""Validate semantic and format projection documents against their schemas."""

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)


def validate_semantic_rules(data: dict[str, Any]) -> None:
    """Enforce semantic rules beyond the document's structural schema."""
    for name, attribute in data.items():
        if not name:
            raise ValueError("Attribute names must not be empty")
        if (attribute["type"] == "array") != ("items" in attribute):
            raise ValueError(f"{name}: items must be present exactly for array types")
        for label, value in (
            (name, attribute),
            (f"{name}.items", attribute.get("items")),
        ):
            if value is not None and "precision" in value and value["type"] != "float":
                raise ValueError(f"{label}: precision is only valid for float")


def validate_json_file(schema_path: Path, json_path: Path) -> bool:
    """Validate one document and report errors at the CLI boundary."""
    try:
        schema = read_json(schema_path)
        data = read_json(json_path)
        jsonschema.validate(data, schema)
        if schema.get("title") == "3DBAG Semantic Attribute Specification Schema":
            validate_semantic_rules(data)
    except (
        OSError,
        ValueError,
        jsonschema.ValidationError,
        jsonschema.SchemaError,
    ) as exc:
        print(f"{json_path}: {exc}")
        return False
    print(f"{json_path}: valid")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", "-s", type=Path, required=True)
    parser.add_argument("--json", "-j", type=Path, required=True)
    args = parser.parse_args()
    if not validate_json_file(args.schema, args.json):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
