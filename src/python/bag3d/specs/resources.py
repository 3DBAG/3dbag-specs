import importlib.resources
from pathlib import Path


def get_resource_file_path(filename: str) -> Path:
    """
    Gets the path to a resource file from the top-level 'resources' directory.

    This function is designed to find resource files that were included at the
    project root (e.g., 'resources/*') via MANIFEST.in.

    Args:
        filename: The name of the file to find in the resources directory.

    Returns:
        A pathlib.Path object pointing to the resource file.
    """
    try:
        package_anchor = importlib.resources.files("bag3d")

        data_path = package_anchor.joinpath("resources", "attributes.json")

        if not data_path.is_file():
            raise FileNotFoundError(
                f"Data file '{filename}' not found at expected path: {data_path}"
            )

        return data_path

    except (ModuleNotFoundError, AttributeError):
        project_root = Path(__file__).resolve().parents[4]
        return project_root.joinpath("resources", filename)
