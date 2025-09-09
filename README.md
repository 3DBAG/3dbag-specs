# 3DBAG Specifications

The 3DBAG Specifications is a single source of truth for the 3DBAG attributes schema.
We use the attribute specifications in our production process to ensure the correct attribute selection and attribute properties, and we use the attribute schema for validating the attributes of the distributed data.

The 3DBAG Specifications is distributed as a python package that you can install with *uv*.

```
uv add git+https://github.com/3DBAG/3dbag-specs --tag v2025.09.03
```

The versioning follows the [3dbag-pipeline](https://github.com/3DBAG/3dbag-pipeline) and consequently the 3DBAG release versions.
For example, *3dbag-specs* version `v2025.09.03` means the version of attributes for the 3DBAG version `v2025.09.03`.

## Usage

See the tests for examples on how to use the library.

## Repository layout

Attribute specification of the 3DBAG.

`resources/attributes.json`: The specification of each 3DBAG attribute.

`resources/attributes.schema.json`: The schema of `attributes.json`. The schema contains the description of each property of the attribute specification.

## License

Licensed under Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0).

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be dual licensed as above, without any additional terms or conditions.

## 3DBAG organisation

This software is part of the 3DBAG project. For more information visit the [3DBAG organisation](https://github.com/3DBAG).
