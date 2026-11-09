"""GeoPackage layer and data-table attribute projections."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from bag3d.specs.resources import load_resource


@dataclass(frozen=True)
class GeoPackageAttribute:
    column: str
    type: str
    encoding: str | None = None


@dataclass(frozen=True)
class LayerSelector:
    city_object_type: str
    geometry_family: str
    lod: str


@dataclass(frozen=True)
class GeoPackageContainer:
    kind: str
    name: str
    selector: LayerSelector | None
    attributes: Mapping[str, GeoPackageAttribute]
    structural_columns: tuple[str, ...]


@dataclass(frozen=True)
class GeoPackageProjection:
    containers: tuple[GeoPackageContainer, ...]
    structural_tables: tuple[str, ...]


def load_geopackage_projection() -> GeoPackageProjection:
    data = load_resource("projections/gpkg.json")
    containers = []
    for container in data["containers"]:
        selector = container.get("selector")
        containers.append(
            GeoPackageContainer(
                kind=container["kind"],
                name=container.get("name", container.get("table")),
                selector=LayerSelector(
                    selector["cityObjectType"],
                    selector["geometryFamily"],
                    selector["lod"],
                )
                if selector
                else None,
                attributes=MappingProxyType(
                    {
                        name: GeoPackageAttribute(
                            entry.get("column", name),
                            entry["type"],
                            entry.get("encoding"),
                        )
                        for name, entry in container["attributes"].items()
                    }
                ),
                structural_columns=tuple(container.get("structuralColumns", ())),
            )
        )
    return GeoPackageProjection(
        tuple(containers), tuple(data.get("structuralTables", ()))
    )
