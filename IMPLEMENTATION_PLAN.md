# Semantic attributes and format projections

The revised migration sequence is:

1. Complete the CityJSON, GeoPackage and OGC 3D Tiles projections from the semantic
   specification and the current exporter. Preserve CityJSON and 3D Tiles
   inclusion, including `b3_val3dity_lod22` in all three tilesets.
2. Replace the combined Python API with semantic and format-specific loaders.
   Update packaged resources, validation and sorting commands, documentation and
   existing tests. Verify an installed wheel with a smoke check.
3. Pin the refactored package in pipeline consumers. Inspect actual serialized
   artifacts, update exporter API references without changing output behavior,
   reuse representative artifacts and update existing Dagster definition checks.

Validation uses schemas, semantic reference checks, one-off comparisons with the
previous specification, existing tests and artifact smoke checks. Migration
comparisons are not permanent tests. Do not add tests that reproduce the
specification, mirror helpers, or assert incidental ordering. Prefer updating
existing coverage and add tests only for consequential behavior that existing
coverage and smoke checks cannot protect.

See README.md for resource contracts and intentional GeoPackage migration changes.
