"""Per-LoD EXT_structural_metadata projections."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from bag3d.specs.resources import load_resource


@dataclass(frozen=True)
class MetadataProperty:
    property: str
    component_type: str
    shape: str
    encoding: str | None
    no_data: int | float | str | bool | None
    null_encoding: str | None


@dataclass(frozen=True)
class Tileset:
    lod: str
    class_name: str
    properties: Mapping[str, MetadataProperty]


@dataclass(frozen=True)
class Ogc3DTilesProjection:
    tilesets: tuple[Tileset, ...]


def load_ogc3dtiles_projection() -> Ogc3DTilesProjection:
    data = load_resource("projections/ogc3dtiles.json")
    return Ogc3DTilesProjection(
        tuple(
            Tileset(
                entry["selector"]["lod"],
                entry["class"],
                MappingProxyType(
                    {
                        name: MetadataProperty(
                            prop.get("property", name),
                            prop["componentType"],
                            prop.get("shape", "scalar"),
                            prop.get("encoding"),
                            prop.get("noData"),
                            prop.get("nullEncoding"),
                        )
                        for name, prop in entry["properties"].items()
                    }
                ),
            )
            for entry in data["tilesets"]
        )
    )
