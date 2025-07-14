from enum import Enum, StrEnum, auto
from typing import Optional
from dataclasses import dataclass


class AttributeType(Enum):
    """3DBAG attribute types."""

    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    DATE = auto()
    DATETIME = auto()
    NULL = auto()

    @classmethod
    def from_string(cls, type_str: str) -> 'AttributeType':
        """Convert string to AttributeType enum."""
        mapping = {
            "int": cls.INT,
            "float": cls.FLOAT,
            "bool": cls.BOOL,
            "string": cls.STRING,
            "date": cls.DATE,
            "datetime": cls.DATETIME,
            "null": cls.NULL,
        }
        return mapping[type_str.lower()]

    def as_python(self) -> str:
        """Convert to Python data type name."""
        mapping = {
            "INT": "int",
            "FLOAT": "float",
            "BOOL": "bool",
            "STRING": "string",
            "DATE": "string",
            "DATETIME": "datetime",
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
            "NULL": "null"
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
            "NULL": "NULL"
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
            "NULL": "NULL"
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
            "NULL": "None"
        }
        return mapping[self.name]


class AttributeAppliesTo(StrEnum):
    """The level where the attribute applies."""

    Building = auto()
    RoofSurface = auto()
    WallSurface = auto()
    GroundSurface = auto()
    ClosureSurface = auto()
    OuterCeilingSurface = auto()
    OuterFloorSurface = auto()
    InteriorWallSurface = auto()
    CeilingSurface = auto()
    FloorSurface = auto()

    @classmethod
    def from_string(cls, applies_to_str: str) -> 'AttributeAppliesTo':
        """Convert string to AttributeAppliesTo enum."""
        # Handle exact matches first
        for item in cls:
            if item.value == applies_to_str:
                return item

        # If no exact match, raise error with suggestions
        raise ValueError(f"Unknown appliesTo value: {applies_to_str}. "
                         f"Valid values: {[item.value for item in cls]}")

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

class DocumentationLanguage(Enum):
    EN = auto()
    NL = auto()

    @classmethod
    def from_string(cls, lang_str: str) -> 'DocumentationLanguage':
        """Convert string to DocumentationLanguage enum."""
        mapping = {
            "en": cls.EN,
            "nl": cls.NL,
        }
        return mapping[lang_str.lower()]


class DocumentationEntry:
    """Documentation entry for an attribute in a specific language."""
    description: str
    type: str


@dataclass
class AttributeValue:
    """Represents a possible value for a categorical attribute."""
    value: str
    description: dict[DocumentationLanguage, str]


@dataclass
class Attribute:
    """3DBAG attribute."""
    type: AttributeType
    source: str
    nullable: bool
    applies_to: AttributeAppliesTo
    precision: Optional[int]
    unit: Optional[str]
    values: Optional[list[AttributeValue]]
    documentation: dict[DocumentationLanguage, DocumentationEntry]
