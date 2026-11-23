set shell := ["bash", "-cu"]

# Run all tests, formatting, lint, and specification checks.
ci: test fmt-check lint check

# Run the test suite with tox.
test:
    tox

# Format files.
fmt:
    uv tool run ruff format

# Check that Python files match Ruff's formatting rules.
fmt-check:
    uv tool run ruff format --check

# Run Ruff lint checks.
lint:
    uv tool run ruff check

# Validate specification JSON files and the attribute bundle.
check:
    for document in resources/semantic/attributes.json resources/projections/{cityjson,gpkg,ogc3dtiles}.json; do uv run validate-specs-json --schema "${document%.json}.schema.json" --json "$document"; done
    uv run validate-specs-bundle resources/attribute-specification.json
