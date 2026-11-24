"""Read JSON relative to the packaged resources root."""

import json
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import PurePosixPath
from typing import Any


def resource_file(relative_path: str) -> Traversable:
    """Find a semantic or projection resource in source and installed packages."""
    path = PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Resource paths must be relative to the resources root")
    resource = files("bag3d.specs.data").joinpath(*path.parts)
    if not resource.is_file():
        raise FileNotFoundError(relative_path)
    return resource


def load_resource(relative_path: str) -> dict[str, Any]:
    return json.loads(resource_file(relative_path).read_text(encoding="utf-8"))
