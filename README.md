# 3DBAG Specifications

The specifications separate the meaning of 3DBAG attributes from their published
representation. Semantic attributes define logical types, descriptions, units,
precision, enumerations, nullability and array items. Each format projection
selects those attributes and specifies their containers, physical names, storage
types and encodings.

Install the package with `uv add /path/to/3dbag-specs` while developing this
breaking release. The package version is `2026.11.09`; release tags follow the
3DBAG release version. The pipeline migration pins a bundled wheel so it can be
used before a remote release is published.

## Python usage

```python
from bag3d.specs.semantic import load_attributes
from bag3d.specs.projections.cityjson import load_cityjson_projection
from bag3d.specs.projections.geopackage import load_geopackage_projection
from bag3d.specs.projections.ogc3dtiles import load_ogc3dtiles_projection

attributes = load_attributes()
cityjson = load_cityjson_projection()
identifier = cityjson.objects["Building"]["identificatie"]
assert attributes["identificatie"].nullable is False
assert identifier.property == "identificatie"

geopackage = load_geopackage_projection()
tilesets = load_ogc3dtiles_projection().tilesets
```

Loaders return frozen models with read-only mappings. Use the defining modules
shown above; `bag3d.specs` has no re-exports. This release removes the previous
combined domain model and its physical type conversion helpers.

## Resources and commands

- `resources/semantic/attributes.json` and its `.schema.json` define semantic attributes.
- `resources/projections/{cityjson,gpkg,ogc3dtiles}.json` and their `.schema.json`
  define the three native format projections.
- `bag3d.specs.resources.resource_file("semantic/attributes.json")` locates a
  packaged resource; paths are relative to the resource root.

The wheel includes all eight JSON documents and schemas. No source checkout is
needed when loading installed resources.

```sh
uv run validate-specs-json -s resources/semantic/attributes.schema.json -j resources/semantic/attributes.json
uv run validate-specs-json -s resources/projections/gpkg.schema.json -j resources/projections/gpkg.json
uv run sort-specs-json -i resources/projections/gpkg.json -o /tmp/gpkg.json
```

Validation checks schemas, duplicate keys and semantic cross-field rules.
Sorting recursively sorts object keys and preserves array order.

## Updating the specification

To add an attribute, add its stable name to the semantic document. Supply `type`,
`description` (Dutch and English), `semanticType`, `source` and boolean `nullable`.
Optional properties are omitted when absent. Arrays require scalar `items` with
its own type, description, semantic type and nullability; nested arrays are not
supported. `precision` applies only to floats, including float array items.
It specifies decimal places, rounded half-to-even in float64 before physical
narrowing. `valueFormat` is descriptive and is never a value-validation pattern.
Years remain integers, including invalid calendar years supplied by the source.

Add the attribute to each intended format container, using the semantic name as
the map key. A physical property/column name defaults to that key when omitted.
Use the actual exporter schema and representative serialized products to choose
physical names, types, encodings and null representations. Validate the changed
JSON against its adjacent schema, check references and physical-name uniqueness,
and run `uv run pytest`. Migration comparisons are one-off checks, not permanent
tests.

CityJSON and 3D Tiles preserve their previous attribute selection, including
`b3_val3dity_lod22` in all three tilesets. Val3dity arrays are currently JSON
strings in both distributions. GeoPackage describes Tyler's current
`building_multisurface_lod0`, three `buildingpart_solid_lod*` layers, `semantics`
and hierarchy tables. Object columns use `attributes__`; semantic columns use
`attribute__`. Booleans are INTEGER, floats REAL, temporal values TEXT, and arrays
JSON TEXT. SQLite REAL does not guarantee float32 storage. Addresses are disabled
by the pipeline's exporter options, so there is no address container in this
projection. The schema supports the exporter's `addresses` table when enabled.

The former GeoPackage-only derived attributes `b3_dd_id`, `b3_pand_deel_id` and
`labels` stay in the semantic catalogue but are not emitted by the current
exporter. BuildingPart identity and surface assignment are represented by
structural columns and hierarchy tables. Schema mismatches in existing products
are reported by validators; this migration does not change producer output.
OBJ remains geometry-only and has no attribute projection.

## License

Licensed under Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE)).
Unless explicitly stated otherwise, contributions are licensed under the same
terms, without additional conditions.
