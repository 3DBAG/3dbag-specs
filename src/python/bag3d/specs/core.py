from enum import Enum, StrEnum, auto
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json
from pathlib import Path

from bag3d.specs.resources import get_resource_file_path


class BaseType(Enum):
    """3DBAG attribute types."""

    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    DATE = auto()
    DATETIME = auto()
    ARRAY = auto()
    NULL = auto()

    @classmethod
    def from_string(cls, type_str: str) -> "BaseType":
        """Convert string to AttributeType enum."""
        mapping = {
            "int": cls.INT,
            "float": cls.FLOAT,
            "bool": cls.BOOL,
            "string": cls.STRING,
            "date": cls.DATE,
            "datetime": cls.DATETIME,
            "array": cls.ARRAY,
            "null": cls.NULL,
        }
        return mapping[type_str.lower()]


@dataclass(frozen=True)
class AttributeType:
    """3DBAG attribute type that can represent simple and complex types.

    >>> simple = AttributeType(BaseType.INT)
    >>> complex = AttributeType(BaseType.ARRAY, BaseType.INT)
    >>> assert complex.as_ogr() == "IntegerList"
    >>> complex = AttributeType.from_dict(
    ...    {
    ...        "type": "array",
    ...        "items": { "type": "string" },
    ...    }
    ... )
    >>> assert complex.as_ogr() == "StringList"
    """

    base_type: BaseType
    sub_type: Optional[BaseType] = None

    def __post_init__(self):
        """Validate type specification."""
        if self.sub_type is not None and self.base_type is None:
            raise ValueError("A sub_type must have a base_type")

    def __str__(self) -> str:
        if self.sub_type:
            return f"{self.base_type.name}<{self.sub_type.name}>"
        return self.base_type.name

    def __repr__(self) -> str:
        if self.sub_type:
            return f"AttributeType({self.base_type.name}, {self.sub_type.name})"
        return f"AttributeType({self.base_type})"

    @classmethod
    def from_dict(cls, data: dict) -> "AttributeType":
        """Create AttributeType from dictionary (for JSON deserialization)."""
        base_type = BaseType.from_string(data["type"])

        if base_type == BaseType.ARRAY and "items" in data:
            item_type = BaseType.from_string(data["items"]["type"])
            return cls(base_type, item_type)

        return cls(base_type)

    def as_json(self) -> str:
        """Convert to JSON data type name."""
        mapping = {
            "INT": "number",
            "FLOAT": "number",
            "BOOL": "boolean",
            "STRING": "string",
            "DATE": "string",
            "DATETIME": "string",
            "ARRAY": "array",
            "NULL": "null",
        }
        return mapping[self.base_type.name]

    def as_python(self) -> str:
        """Convert to Python data type name."""
        mapping = {
            "INT": "int",
            "FLOAT": "float",
            "BOOL": "bool",
            "STRING": "str",
            "DATE": "date",
            "DATETIME": "datetime",
            "ARRAY": "list",
            "NULL": "None",
        }
        return mapping[self.base_type.name]

    def as_gpkg(self) -> str:
        """Convert to GeoPackage data type name."""
        mapping = {
            "INT": "INTEGER",
            "FLOAT": "FLOAT",
            "BOOL": "BOOLEAN",
            "STRING": "TEXT",
            "DATE": "DATE",
            "DATETIME": "DATETIME",
            "ARRAY": "TEXT",
            "NULL": "NULL",
        }
        return mapping[self.base_type.name]

    def as_ogr(self) -> str:
        """Convert to OGR Field data type, including the subtype where relevant.

        References:
            - Schema for OGR_SCHEMA open option: https://raw.githubusercontent.com/OSGeo/gdal/refs/heads/master/ogr/data/ogr_fields_override.schema.json
            - OGR Field subtypes RFC: https://gdal.org/en/stable/development/rfc/rfc50_ogr_field_subtype.html
        """
        mapping_subtype = {
            "INT": "Integer",
            "FLOAT": "Real",
            "STRING": "String",
        }
        if self.base_type == BaseType.ARRAY:
            if subtype := mapping_subtype.get(self.sub_type.name):
                return f"{subtype}List"
        mapping = {
            "INT": "Integer",
            "FLOAT": "Real",
            "BOOL": "Integer(Boolean)",
            "STRING": "String",
            "DATE": "Date",
            "DATETIME": "DateTime",
            "NULL": "String",
        }
        return mapping[self.base_type.name]


class CityJSONLocation(StrEnum):
    """The object type where the attribute is located in CityJSON.

    Attributes:
        Building
        BuildingPart
        RoofSurface
        WallSurface
        GroundSurface
        ClosureSurface
        OuterCeilingSurface
        OuterFloorSurface
        InteriorWallSurface
        CeilingSurface
        FloorSurface
    """

    Building = "Building"
    BuildingPart = "BuildingPart"
    RoofSurface = "RoofSurface"
    WallSurface = "WallSurface"
    GroundSurface = "GroundSurface"
    ClosureSurface = "ClosureSurface"
    OuterCeilingSurface = "OuterCeilingSurface"
    OuterFloorSurface = "OuterFloorSurface"
    InteriorWallSurface = "InteriorWallSurface"
    CeilingSurface = "CeilingSurface"
    FloorSurface = "FloorSurface"

    @classmethod
    def from_string(cls, cityjson_location_str: str) -> "CityJSONLocation":
        """Convert a string to CityJSONLocation enum."""
        for item in cls:
            if item.value == cityjson_location_str:
                return item

        raise ValueError(
            f"Unknown CityJSONLocation value: {cityjson_location_str}. "
            f"Valid values: {[item.value for item in cls]}"
        )


class GpkgLocation(StrEnum):
    """The GeoPackage layer where the attribute is located."""

    pand = "pand"
    lod12_2d = "lod12_2d"
    lod12_3d = "lod12_3d"
    lod13_2d = "lod13_2d"
    lod13_3d = "lod13_3d"
    lod22_2d = "lod22_2d"
    lod22_3d = "lod22_3d"

    @classmethod
    def from_string(cls, gpkg_location_str: str) -> "GpkgLocation":
        """Convert a string to GpkgLocation enum."""
        for item in cls:
            if item.value == gpkg_location_str:
                return item

        raise ValueError(
            f"Unknown GpkgLocation value: {gpkg_location_str}. "
            f"Valid values: {[item.value for item in cls]}"
        )


@dataclass
class AttributeAppliesTo:
    """The appliesTo property."""

    cityjson: Optional[dict] = None
    gpkg: Optional[dict] = None

    @classmethod
    def from_dict(cls, data: dict) -> "AttributeAppliesTo":
        cityjson = None
        gpkg = None
        if cj := data.get("cityjson"):
            cityjson = {
                "locations": list(map(CityJSONLocation.from_string, cj["locations"]))
            }
        if g := data.get("gpkg"):
            gpkg = {"locations": list(map(GpkgLocation.from_string, g["locations"]))}
        return cls(cityjson=cityjson, gpkg=gpkg)


class DocumentationLanguage(Enum):
    EN = auto()
    NL = auto()

    @classmethod
    def from_string(cls, lang_str: str) -> "DocumentationLanguage":
        """Convert string to DocumentationLanguage enum."""
        mapping = {
            "en": cls.EN,
            "nl": cls.NL,
        }
        return mapping[lang_str.lower()]


@dataclass
class Translation:
    """Translation in Dutch and English."""

    nl: str
    en: str

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Translation":
        """Create Translation from dictionary."""
        return cls(nl=data["nl"], en=data["en"])


@dataclass
class ArrayItemDefinition:
    """Definition for items in an array-type attribute."""

    type: AttributeType
    semantic_type: Optional[str] = None
    description: Optional[Translation] = None
    scale: Optional[Translation] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArrayItemDefinition":
        """Create ArrayItemDefinition from dictionary."""
        return cls(
            type=AttributeType(data["type"]),
            semantic_type=data.get("semanticType"),
            description=Translation.from_dict(data["description"])
            if "description" in data
            else None,
            scale=Translation.from_dict(data["scale"]) if "scale" in data else None,
        )


@dataclass
class Attribute:
    """3DBAG attribute.

    Attributes:
        name: str
        type: AttributeType
        source: Optional[str]
        nullable: bool
        applies_to: AttributeAppliesTo
        precision: Optional[int]
        unit: Optional[Translation]
        value_format: Optional[str]
        semantic_type: str
        values: Optional[Dict[str, Translation]]
        description: Translation
        scale: Optional[Translation]
        items: Optional[ArrayItemDefinition]
    """

    name: str
    type: AttributeType
    source: Optional[str]
    nullable: bool
    applies_to: AttributeAppliesTo
    precision: Optional[int]
    unit: Optional[Translation]
    value_format: Optional[str]
    semantic_type: str
    values: Optional[Dict[str, Translation]]
    description: Translation
    scale: Optional[Translation]
    items: Optional[ArrayItemDefinition]

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "Attribute":
        """Create Attribute from dictionary."""
        # Handle values - can be null or a dict of value: translation pairs
        values = None
        if data.get("values") is not None:
            values = {
                key: Translation.from_dict(val) for key, val in data["values"].items()
            }

        # Handle optional Translation fields
        unit = (
            Translation.from_dict(data["unit"])
            if data.get("unit") is not None
            else None
        )
        scale = (
            Translation.from_dict(data["scale"])
            if data.get("scale") is not None
            else None
        )

        # Handle array items
        items = None
        if "items" in data and data["items"] is not None:
            items = ArrayItemDefinition.from_dict(data["items"])

        return cls(
            name=name,
            type=AttributeType.from_dict(data),
            source=data["source"],
            nullable=data["nullable"],
            applies_to=AttributeAppliesTo.from_dict(data["appliesTo"]),
            precision=data["precision"],
            unit=unit,
            value_format=data["valueFormat"],
            semantic_type=data["semanticType"],
            values=values,
            description=Translation.from_dict(data["description"]),
            scale=scale,
            items=items,
        )


def load_attributes_from_json(json_path: Path) -> Dict[str, Attribute]:
    """
    Load attributes from a JSON file and deserialize them into a dictionary.

    Args:
        json_path: Path to the JSON file containing attribute definitions.

    Returns:
        A dictionary where keys are attribute names and values are Attribute objects.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    attributes = {}
    for attr_name, attr_data in data.items():
        attributes[attr_name] = Attribute.from_dict(attr_name, attr_data)

    return attributes


def load_attributes_spec_schema() -> dict:
    """Load the attribute specifications schema from the package."""
    path_attributes_json = get_resource_file_path("attributes.schema.json")
    with open(path_attributes_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def load_attributes_spec() -> Dict[str, Attribute]:
    """Load the attribute specifications from the package.

    Returns:
        A dictionary where keys are attribute names and values are Attribute objects.
    """
    path_attributes_json = get_resource_file_path("attributes.json")
    return load_attributes_from_json(path_attributes_json)
