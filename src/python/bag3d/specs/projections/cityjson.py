"""CityJSON object and semantic-surface attribute projections."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from bag3d.specs.resources import load_resource


@dataclass(frozen=True)
class CityJSONAttribute:
    property: str
    type: str
    encoding: str | None = None


@dataclass(frozen=True)
class CityJSONProjection:
    objects: Mapping[str, Mapping[str, CityJSONAttribute]]
    semantic_surfaces: Mapping[str, Mapping[str, CityJSONAttribute]]


def _containers(data: dict) -> Mapping[str, Mapping[str, CityJSONAttribute]]:
    return MappingProxyType(
        {
            location: MappingProxyType(
                {
                    name: CityJSONAttribute(
                        entry.get("property", name),
                        entry["type"],
                        entry.get("encoding"),
                    )
                    for name, entry in container["attributes"].items()
                }
            )
            for location, container in data.items()
        }
    )


def load_cityjson_projection() -> CityJSONProjection:
    data = load_resource("projections/cityjson.json")
    return CityJSONProjection(
        _containers(data["objects"]), _containers(data.get("semanticSurfaces", {}))
    )
