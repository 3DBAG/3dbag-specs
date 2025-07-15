from enum import Enum, StrEnum, auto
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json
from pathlib import Path

from .resources import get_resource_file_path


class AttributeType(Enum):
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
    def from_string(cls, type_str: str) -> "AttributeType":
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

    def as_python(self) -> str:
        """Convert to Python data type name."""
        mapping = {
            "INT": "int",
            "FLOAT": "float",
            "BOOL": "bool",
            "STRING": "str",
            "DATE": "str",
            "DATETIME": "datetime",
            "ARRAY": "list",
            "NULL": "None",
        }
        return mapping[self.name]

    def as_cpp(self) -> str:
        """Convert to C++ data type name."""
        mapping = {
            "INT": "int",
            "FLOAT": "float",
            "BOOL": "bool",
            "STRING": "string",
            "DATE": "string",
            "DATETIME": "string",
            "ARRAY": "vector",
            "NULL": "null",
        }
        return mapping[self.name]

    def as_postgresql(self) -> str:
        """Convert to PostgreSQL data type name."""
        mapping = {
            "INT": "INTEGER",
            "FLOAT": "DOUBLE PRECISION",
            "BOOL": "BOOLEAN",
            "STRING": "TEXT",
            "DATE": "DATE",
            "DATETIME": "TIMESTAMP",
            "ARRAY": "ARRAY",
            "NULL": "NULL",
        }
        return mapping[self.name]

    def as_gpkg(self) -> str:
        """Convert to GeoPackage data type name."""
        mapping = {
            "INT": "INTEGER",
            "FLOAT": "DOUBLE",
            "BOOL": "BOOLEAN",
            "STRING": "TEXT",
            "DATE": "DATE",
            "DATETIME": "DATETIME",
            "ARRAY": "TEXT",
            "NULL": "NULL",
        }
        return mapping[self.name]

    def as_rust(self) -> str:
        """Convert to Rust data type name."""
        mapping = {
            "INT": "i32",
            "FLOAT": "f64",
            "BOOL": "bool",
            "STRING": "String",
            "DATE": "String",
            "DATETIME": "String",
            "ARRAY": "Vec",
            "NULL": "None",
        }
        return mapping[self.name]


class AttributeAppliesTo(StrEnum):
    """The level where the attribute applies."""

    Building = "Building"
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
    def from_string(cls, applies_to_str: str) -> "AttributeAppliesTo":
        """Convert string to AttributeAppliesTo enum."""
        # Handle exact matches first
        for item in cls:
            if item.value == applies_to_str:
                return item

        # If no exact match, raise error with suggestions
        raise ValueError(
            f"Unknown appliesTo value: {applies_to_str}. "
            f"Valid values: {[item.value for item in cls]}"
        )


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
            type=AttributeType.from_string(data["type"]),
            semantic_type=data.get("semanticType"),
            description=Translation.from_dict(data["description"])
            if "description" in data
            else None,
            scale=Translation.from_dict(data["scale"]) if "scale" in data else None,
        )


@dataclass
class Attribute:
    """3DBAG attribute."""

    name: str
    type: AttributeType
    source: Optional[str]
    nullable: bool
    applies_to: AttributeAppliesTo
    precision: Optional[int]
    unit: Optional[Translation]
    format: Optional[str]
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
            type=AttributeType.from_string(data["type"]),
            source=data["source"],
            nullable=data["nullable"],
            applies_to=AttributeAppliesTo.from_string(data["appliesTo"]),
            precision=data["precision"],
            unit=unit,
            format=data["format"],
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


def load_attributes_spec() -> Dict[str, Attribute]:
    """Load the attribute specifications from the package.

    Returns:
        A dictionary where keys are attribute names and values are Attribute objects.
    """
    path_attributes_json = get_resource_file_path("attributes.json")
    return load_attributes_from_json(path_attributes_json)
