from importlib.resources import files
from pathlib import Path
import sys


def get_resource_file_path(filename: str) -> Path:
    """Get the path to the resources directory."""
    # In installed package, resources are in site-packages/bag3d/resources/
    resource_path = Path(sys.prefix) / "share" / "bag3d" / "resources" / filename
    if resource_path.exists():
        return resource_path

    # Fallback for development (when running from source)
    resource_path = Path(files("bag3d.specs").name).parent.parent.joinpath(
        "resources", filename
    )
    if resource_path.exists():
        return resource_path

    raise FileNotFoundError(f"Resource file {filename} is not found at {resource_path}")
