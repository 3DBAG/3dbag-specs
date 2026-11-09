# Semantic attributes and format projections: implementation plan

## Objective

Refactor `3dbag-specs` so that it contains two separate kinds of specification:

1. A format-independent semantic model of 3D BAG attributes.
2. Checked-in format projections that define how those attributes are selected,
   located, named, and serialized in each distribution format.

The refactored package will expose both specifications to `3dbag-pipeline`.
Pipeline validators will use them to determine the expected schema and will
establish conformance by inspecting the serialized output itself.

This is a breaking redesign. The existing `appliesTo` model and format-specific
serialization methods will be removed instead of preserved behind compatibility
wrappers.

## Current status (work in progress)

Already implemented on disk (uncommitted, branch `split-representations`):

- `resources/semantic/attributes.schema.json` — new semantic schema implementing
  all pinned decisions (see "Pinned decisions from the plan review" below).
- `resources/semantic/attributes.json` — all 66 attributes migrated from
  `resources/attributes.json`: `appliesTo` removed, null-valued optional keys
  dropped, `nullable` made an explicit boolean (6 former nulls set to `true`),
  `items` given explicit `nullable: false`, canonical key order.
- `resources/projections/{cityjson,gpkg,ogc3dtiles}.schema.json` — projection
  schemas implementing the pinned projection-shape decisions (see "Pinned
  projection-shape decisions" below).
- `tests/fixtures/projections/{cityjson,gpkg,ogc3dtiles}.json` — test fixtures
  covering 12 edge-case attributes (`b3_h_nok`, `identificatie`, `b3_h_50p`,
  `b3_val3dity_lod22`, `b3_dd_id`, `b3_dak_type`, `b3_kwaliteitsindicator`,
  `b3_pw_datum`, `eindregistratie`, `oorspronkelijkbouwjaar`, `b3_azimut`,
  `b3_rmse_lod22`), generated from the current `appliesTo` data. They cover every
  logical type x format combination, semantic-surface containers, per-LoD
  tilesets, gpkg-only and 3D-Tiles-absent attributes, bool enums with
  string keys, temporal types, and the two pinned `valueFormat` anomalies.

Validation performed (all passing):

- `resources/semantic/attributes.json` validates against the new semantic schema
  (jsonschema, draft-07), plus cross-field rules the schema cannot express:
  `items` present iff `type` is `array`, `precision` only on `float`, no nested
  arrays, no empty attribute names.
- Each projection fixture validates against its projection schema, plus
  cross-file checks: every referenced attribute exists in the semantic file,
  physical names unique per container, physical type compatible with logical
  type per the pinned mapping. Negative tests confirmed the checks reject a
  wrong physical type, a `selector` on a `semantics` container, and a `layer`
  without `name`.

Not yet done: full 66-attribute projection instances in
`resources/projections/*.json`; the `core.py` -> `semantic.py` +
`projections/` Python split and loaders; the `validate_json.py`/`sort_json.py`
rename with `[project.scripts]` update; pyproject package data; README; tests;
Phase 5 pipeline migration. The old `resources/attributes.json` and
`attributes.schema.json` are intentionally still in place.

## Design principles

- Keep semantic meaning separate from physical representation.
- Keep all authoritative specifications as reviewed JSON files in Git.
- Use JSON Schema to validate each specification file.
- Do not introduce a schema compiler or generated intermediate contracts.
- Treat the serialized artifact as the authority for what was actually written.
- Do not change producers or serializers as part of this implementation.
- Give every public symbol one canonical import path.
- Keep format-specific concepts out of the semantic Python model.

## Target repository layout

```text
resources/
├── semantic/
│   ├── attributes.json
│   └── attributes.schema.json
└── projections/
    ├── cityjson.json
    ├── cityjson.schema.json
    ├── gpkg.json
    ├── gpkg.schema.json
    ├── ogc3dtiles.json
    └── ogc3dtiles.schema.json

src/python/bag3d/specs/
├── __init__.py
├── semantic.py
├── resources.py
├── projections/
│   ├── __init__.py
│   ├── cityjson.py
│   ├── gpkg.py
│   └── ogc3dtiles.py
├── sort_json.py
└── validate_json.py
```

OBJ is intentionally absent from the first set of projections because the current
OBJ distribution is geometry-only. Add an OBJ projection only if OBJ gains
attributes or format-specific attribute configuration.

## Specification boundaries

### Semantic attributes

`resources/semantic/attributes.json` owns properties that remain true regardless
of distribution format:

- Stable attribute identifier.
- Logical value type.
- Description and translations.
- Semantic type.
- Source.
- Unit and scale.
- Precision or accuracy requirements.
- Value format.
- Enumerated values.
- Nullability.
- Array item semantics.

It must not contain:

- `appliesTo`.
- Format names.
- Layer, object, property, or tileset locations.
- OGR, SQLite, JSON, Geoflow, glTF, or 3D Tiles physical types.
- Physical field names or serializer options.

The existing attribute names remain the stable identifiers. A separate `id` field
is unnecessary while the JSON object is keyed by that identifier.

#### Pinned decisions from the plan review

These decisions are locked in; `resources/semantic/attributes.schema.json` and
`resources/semantic/attributes.json` already implement them:

- **Required vs optional.** Required: `type`, `description`, `semanticType`,
  `source`, `nullable` (a boolean). Optional (absent means none): `unit`,
  `precision`, `scale`, `valueFormat`, `values`, `items`. `appliesTo` is gone from
  the semantic file entirely. The six attributes that had `nullable: null`
  (`b3_azimut`, `b3_hellingshoek`, `b3_h_50p`, `b3_h_70p`, `b3_h_max`, `b3_h_min`)
  are now explicitly `nullable: true`.
- **`valueFormat` is optional and descriptive only.** strftime pattern for
  `date`/`datetime`, free-form pattern otherwise. It is never validated against
  data values, and serializers may rely on it only for temporal types;
  non-temporal behavior is driven by `type` + `semanticType`.
  `oorspronkelijkbouwjaar` is intentionally `int` + `"YYYY"` because source data
  contains invalid years (e.g. `9999`) that must be preserved, not parsed as
  dates. `b3_pw_datum` stays `date` (always a valid date). No separate regex
  `pattern` field: deferred until a concrete consumer needs machine-checkable
  patterns, then with a pinned regex flavor and precedence rules.
- **`precision`** means maximum digits after the decimal point (range 0-17),
  rounded half-to-even in float64 first, then narrowed to the physical type the
  projection declares (never narrow-then-round). Valid only on `float`; the
  validator rejects it on other types.
- **Array `items`** reuse a shared `value` definition: `attribute = value +
  source + items`, `items = value`. No array-of-arrays. The item-only `"null"`
  type is dropped in favor of item-level `nullable`. `additionalProperties:
  false` everywhere, and empty attribute names are rejected (`propertyNames`
  plus a validator check, since JSON duplicate keys are otherwise silent).
- **Coverage.** There is no CityJSONSeq distribution, so no `cityjsonseq`
  projection or format id exists. In the GeoPackage projection, only true
  GeoPackage system/metadata tables (`gpkg_*`, rtree, ...) are structural; the
  `semantics` and `address` tables are named containers because they carry
  attribute values. One rule: every location where a spec attribute can appear
  is named in the projection.

### Format projections

Each projection owns the complete mapping from semantic attributes to one physical
format:

- Which semantic attributes are included.
- Their physical container or location.
- Their serialized field/property name.
- Their physical type where the format exposes one.
- Format-specific null representation.
- Format-specific value transformations.
- Container naming or selection rules required to locate the serialized value.

Projections reference semantic constraints instead of repeating them. For example,
an attribute's logical type and nullability remain in the semantic model, while a
projection specifies the target storage type and how that format represents a
semantic null. Pipeline validators read both files when checking an artifact.

Each format gets its own JSON Schema. Avoid a universal projection model: CityJSON
objects, GeoPackage layers, and 3D Tiles metadata have materially different
structures and should be described in their native terms.

## Proposed projection shapes

The exact field names must be derived from the current serialized products and
agreed publication schema. These examples establish the intended ownership and
level of detail.

Pinned projection-shape decisions (implemented by the schemas in
`resources/projections/`, exercised by fixtures in `tests/fixtures/projections/`):

- Format ids are the existing `appliesTo` keys: `cityjson`, `gpkg`,
  `ogc3dtiles` (no `cityjsonseq`). Files are named `<format>.json` /
  `<format>.schema.json`.
- All projections share one envelope and one per-attribute contract:
  `{ "format": "<id>", ...containers... }`, each attribute entry referencing a
  semantic attribute with a physical name (`property`/`column`, defaulting to
  the attribute name when absent), a physical type in the format's own
  vocabulary, and (3D Tiles) a `shape`. Only the container model differs per
  format; there is deliberately no universal projection model.
- Physical type vocabularies follow the existing `AttributeType.as_*()`
  mappings: CityJSON `string|number|boolean|array|object`; GeoPackage
  `TEXT|INTEGER|FLOAT|REAL|BOOLEAN|DATE|DATETIME` (arrays as TEXT/JSON);
  3D Tiles EXT_structural_metadata `componentType`
  (`INT8..UINT64|FLOAT32|FLOAT64|STRING|BOOLEAN`) plus `shape: scalar|array`.
- GeoPackage containers: `kind: layer` requires `name`; `selector`
  (`cityObjectType`, `geometryFamily`, `lod`) is allowed only on layers and only
  when the name is derived — the schema forbids `selector`/`name` on
  `semantics`/`address`, which use a fixed `table`. Cross-file tests verify
  selector expansion against declared names.
- OGC 3D Tiles containers are tilesets (`selector.lod` + `class` + `properties`),
  not bare classes, so per-LoD applicability (e.g. `b3_val3dity_lod22` only in
  the lod22 tileset) is expressible.

### CityJSON

```json
{
  "format": "cityjson",
  "objects": {
    "Building": {
      "attributes": {
        "identificatie": {
          "property": "identificatie",
          "type": "string"
        }
      }
    },
    "BuildingPart": {
      "attributes": {
        "b3_h_dak_max": {
          "property": "b3_h_dak_max",
          "type": "number"
        }
      }
    }
  },
  "semanticSurfaces": {
    "RoofSurface": {
      "attributes": {
        "b3_azimut": {
          "property": "b3_azimut",
          "type": "number"
        }
      }
    }
  }
}
```

CityJSON's projection must not pretend that JSON numbers have a `float32` or
`float64` representation. It may define numeric rounding or significant-digit
rules when those are part of the published product.

### GeoPackage

```json
{
  "format": "geopackage",
  "layers": [
    {
      "selector": {
        "cityObjectType": "BuildingPart",
        "geometryFamily": "MultiSurface",
        "lod": "2.2"
      },
      "name": "BuildingPart_MultiSurface_lod22",
      "attributes": {
        "identificatie": {
          "column": "identificatie",
          "type": "TEXT"
        }
      }
    }
  ]
}
```

The GeoPackage projection must describe the current generated layers rather than the
legacy `pand` and `lod*_2d`/`lod*_3d` layout. If layer names are derived rather
than enumerated, represent the derivation once as a constrained naming template
and test its expansion against concrete examples. The `semantics` and `address`
tables are named containers in the projection (they carry attribute values);
only GeoPackage system tables are structural and ignored by validators.

GeoPackage physical types must reflect what SQLite/GeoPackage actually stores.
For example, SQLite `REAL` is an eight-byte IEEE floating-point value; a declared
`FLOAT` affinity must not be presented as guaranteed float32 storage.

### OGC 3D Tiles

```json
{
  "format": "ogc3dtiles",
  "classes": {
    "building": {
      "properties": {
        "b3_h_dak_max": {
          "property": "b3_h_dak_max",
          "componentType": "FLOAT32"
        }
      }
    }
  }
}
```

The projection must use the physical types supported by the selected 3D Tiles
metadata representation and distinguish scalar, vector, array, enum, and string
properties where required.

## Phase 1: lock down the new resource contracts

1. Create `resources/semantic/attributes.schema.json` by removing `appliesTo` and
   all format-specific definitions from the current schema.
2. Move the semantic properties from `resources/attributes.json` into
   `resources/semantic/attributes.json` and remove every `appliesTo` value.
3. Create one projection schema and projection file per supported attributed
   format: CityJSON, GeoPackage, and OGC 3D Tiles.
4. Migrate every existing `appliesTo` entry into the relevant projection without
   changing attribute inclusion unintentionally.
5. Replace legacy GeoPackage locations with the current layer model during the
   migration; do not encode the old layer names in the new projection.
6. Add explicit physical types to each projected attribute. Resolve every type
   using the target format's actual storage capabilities rather than the old
   `AttributeType.as_*()` mappings.
7. Define explicit behavior for any intentional narrowing or transformation,
   including numeric rounding, integer range, enum representation, date/time
   representation, arrays, nulls, and unsupported values.

Deliverable: all semantic and projection JSON files validate independently against
their JSON Schemas.

## Phase 2: add cross-file conformance checks

JSON Schema cannot validate references between files, so add small, direct tests
for these invariants:

- Every attribute referenced by a projection exists in
  `resources/semantic/attributes.json`.
- Every projected physical name is unique within its container.
- Every projection location/container is legal for its format.
- Every physical type is supported by that format.
- Every projected physical type is compatible with the semantic attribute's
  logical type (e.g. semantic `array` -> CityJSON array but GeoPackage
  JSON-TEXT; semantic `bool` -> GeoPackage `BOOLEAN` vs OGR
  `Integer(Boolean)`).
- Every semantic attribute intended for publication is projected into at least one
  format, unless it is explicitly marked internal in the semantic model.
- Projection selectors and naming templates produce unique containers.
- Existing expected attribute sets are preserved for CityJSON and OGC 3D Tiles.
- The GeoPackage attribute sets match the current serialized schema.

Keep these checks as repository tests. They load the checked-in JSON directly;
they do not generate another schema representation.

## Phase 3: replace the Python domain model

1. Split `core.py` into `semantic.py` and format-specific modules under
   `projections/`.
2. Keep `BaseType`, `AttributeType`, `Attribute`, `Translation`, and array item
   definitions in `semantic.py`, updated for the new semantic JSON.
3. Remove `AttributeAppliesTo`, `CityJSONLocation`, `GpkgLocation`, and
   `Ogc3dTilesLocation` from the semantic module.
4. Remove `AttributeType.as_json()`, `as_gpkg()`, `as_ogr()`, and `as_geof()`.
   Physical type mappings belong in projections and artifact validators.
5. Retain a Python type helper only if a current Python consumer needs it for
   validating in-memory semantic values; name it accordingly rather than treating
   Python as a distribution format.
6. Add thin, typed loaders:
   - `load_attributes()`
   - `load_cityjson_projection()`
   - `load_geopackage_projection()`
   - `load_ogc3dtiles_projection()`
7. Model only fields that consumers use. Do not introduce a generic projection
   inheritance hierarchy or compiler abstraction.
8. Keep `bag3d.specs.__init__` empty and use canonical module import paths.
9. Replace `get_resource_file_path(filename)` with resource functions that make
   the semantic/projection distinction explicit, or require paths relative to the
   `resources` root.

This phase intentionally breaks imports from `bag3d.specs.core`. Update all known
consumers in the same migration rather than adding aliases or deprecated wrappers.

## Phase 4: simplify validation and packaging

1. Replace the attribute-specific validation CLI with a general command capable of
   validating each checked-in semantic or projection JSON file against its schema.
   The validator also enforces the cross-field rules JSON Schema draft-07 cannot
   express: `items` present iff `type` is `array`, `precision` only on `float`,
   and no empty-string attribute names. Rename `validate_attributes_json.py` /
   `sort_attributes.py` to `validate_json.py` / `sort_json.py` and update
   `[project.scripts]` in the same commit.
2. Make text encoding explicit for all JSON reads.
3. Update sorting so it can sort semantic attributes and deterministic projection
   maps without rewriting meaningful ordered arrays such as layer priority.
4. Update `pyproject.toml` package data to include the complete semantic and
   projection resource trees.
5. Update `README.md` with:
   - The semantic/projection distinction.
   - The repository layout.
   - Canonical Python loading examples.
   - Instructions for adding an attribute.
   - Instructions for adding or changing a format projection.
6. Replace tests of `appliesTo` and location enums with semantic-loader,
   projection-loader, JSON Schema, and cross-file conformance tests.
7. Add a wheel-install test proving that every resource can be found after package
   installation, not only from a source checkout.

## Phase 5: migrate `3dbag-pipeline` validation

Implement this phase after publishing or pinning the refactored `bag3d-specs`
package. This phase changes schema selection and validation only; export producer
configuration is out of scope.

1. Replace `Specs3DBAGResource.applies_to()` with explicit semantic and projection
   accessors. Load each resource once and expose immutable mappings to validation
   code.
2. Remove imports of `AttributeAppliesTo`, `CityJSONLocation`, `GpkgLocation`, and
   `Ogc3dTilesLocation` from pipeline code.
3. Add format-specific helpers that select expected attributes for a concrete
   CityJSON object/surface, GeoPackage layer, or 3D Tiles metadata class. Keep
   container matching in these helpers instead of scattering projection traversal
   across validation functions.
4. Update CityJSON validation to:
   - Select expected properties from the CityJSON projection.
   - Compare missing and extra properties per CityObject and semantic surface.
   - Validate observed JSON value types against projected physical types.
   - Validate values, nullability, enumerations, and semantic constraints against
     the semantic attribute model.
5. Replace the GeoPackage validation path so that it:
   - Verifies and opens the compressed tile artifact before schema validation.
   - Obtains the actual layer and field schema through machine-readable GDAL output.
   - Matches observed layers to projection layer names or selectors.
   - Reports missing and unexpected layers explicitly.
   - Compares projected columns, physical types, and nullability with observed
     fields while separating format structural columns from projected attributes.
   - Calculates building, building-part, and invalid-geometry counts from the
     matched observed layers rather than hard-coded `lod12_3d`, `lod13_3d`, and
     `lod22_3d` lists.
   - Reads aggregate query results through SQLite or another structured result API.
     Do not parse presentation-oriented `ogrinfo` text with exact regular
     expressions.
6. Update OGC 3D Tiles validation to inspect the serialized tileset and compare
   metadata classes, property names, scalar/array shape, component types, and null
   behavior with the OGC 3D Tiles projection. Add a dedicated validation asset if
   the existing compressed-tile validation asset does not receive these outputs.
7. Keep the existing geometry-only OBJ validation separate from attribute
   projections. Its archive and geometry checks remain in scope, but it must not
   acquire an empty attribute projection merely for API uniformity.
8. Make all validation aggregation total:
   - Never call `min()`, `max()`, or equivalent operations before checking that a
     result collection is non-empty.
   - Treat an empty collection as a contextual validation failure naming the tile,
     format, query, and observed layers.
   - Preserve the tile identifier when propagating exceptions from
     `ProcessPoolExecutor` workers.
9. Return validation outcomes for schema mismatches. Reserve exceptions for files
   that cannot be opened, malformed projections, unsupported inspection paths, and
   other cases where validation cannot complete.
10. Add focused unit tests for projection-based attribute selection and each
    format inspector. Include missing/extra fields, incorrect physical types, nulls,
    unknown layers/classes, empty query results, and malformed archives.
11. Add integration fixtures representing one current serialized tile per format.
    Validate the actual CityJSON, GeoPackage, and OGC 3D Tiles artifacts through the
    same functions used by the Dagster assets.
12. Update Dagster definition tests so the export code location loads with the new
    specs API and all validation asset dependencies resolve.
13. Remove fallback handling for the old schema after all pipeline call sites have
    migrated.

## Verification gates

The refactor is complete when:

- Every checked-in JSON file validates against its JSON Schema.
- All cross-file projection references and uniqueness constraints pass.
- The Python package tests pass from both the source tree and an installed wheel.
- The package contains all resource files after installation.
- CityJSON validation reads actual objects and surfaces and detects projected
  property and value-type mismatches.
- GeoPackage validation discovers the current layers, validates their fields, and
  completes aggregate counts without parsing human-readable command output.
- OGC 3D Tiles validation inspects actual metadata classes and physical property
  encodings.
- Pipeline validators inspect actual artifacts and use no legacy layer/location
  enums.
- Repository-wide search finds no `appliesTo`, `AttributeAppliesTo`,
  `CityJSONLocation`, `GpkgLocation`, `Ogc3dTilesLocation`, `as_gpkg`, `as_ogr`, or
  `as_geof` references outside historical release notes.

## Suggested implementation sequence

Keep the work reviewable with commits in this order:

1. Add semantic and projection schemas with minimal representative fixtures.
2. Migrate all attribute applicability data into projections.
3. Add cross-file conformance tests.
4. Replace the Python model and loaders.
5. Update packaging, CLI tools, tests, and documentation.
6. Publish a breaking `bag3d-specs` release and pin it in `3dbag-pipeline`.
7. Migrate pipeline validators and remove all legacy API usage.
8. Verify Dagster definitions and validation against current serialized fixtures.

Do not keep the old and new models alive in parallel beyond the short period needed
to coordinate `3dbag-specs` and `3dbag-pipeline`. The final state must have one
semantic model,
one projection per attributed format, and no compatibility layer.
