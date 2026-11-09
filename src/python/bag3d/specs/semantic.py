"""Format-independent meanings and constraints of published attributes."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Self

from bag3d.specs.resources import load_resource
from bag3d.specs.validate_json import read_json, validate_semantic_rules


class BaseType(StrEnum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    DATE = "date"
    DATETIME = "datetime"
    ARRAY = "array"

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls(value.lower())


@dataclass(frozen=True)
class AttributeType:
    base_type: BaseType
    sub_type: BaseType | None = None

    def __post_init__(self) -> None:
        if (self.base_type == BaseType.ARRAY) != (self.sub_type is not None):
            raise ValueError("Only array types require a scalar item type")
        if self.sub_type == BaseType.ARRAY:
            raise ValueError("Nested arrays are unsupported")

    def __str__(self) -> str:
        if self.sub_type is not None:
            return f"{self.base_type.name}<{self.sub_type.name}>"
        return self.base_type.name

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            BaseType(data["type"]),
            BaseType(data["items"]["type"]) if data["type"] == "array" else None,
        )


class DocumentationLanguage(StrEnum):
    EN = "en"
    NL = "nl"

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls(value.lower())


@dataclass(frozen=True)
class Translation:
    nl: str
    en: str

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(nl=data["nl"], en=data["en"])

    def get_translation(self, lang: DocumentationLanguage) -> str:
        return getattr(self, lang.value)


def _optional_translation(data: dict[str, Any], key: str) -> Translation | None:
    return Translation.from_dict(data[key]) if key in data else None


def _values(data: dict[str, Any]) -> Mapping[str, Translation] | None:
    if "values" not in data:
        return None
    return MappingProxyType(
        {key: Translation.from_dict(value) for key, value in data["values"].items()}
    )


@dataclass(frozen=True, kw_only=True)
class ArrayItemDefinition:
    type: AttributeType
    semantic_type: str
    description: Translation
    nullable: bool
    unit: Translation | None = None
    precision: int | None = None
    scale: Translation | None = None
    value_format: str | None = None
    values: Mapping[str, Translation] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            type=AttributeType.from_dict(data),
            semantic_type=data["semanticType"],
            description=Translation.from_dict(data["description"]),
            nullable=data["nullable"],
            unit=_optional_translation(data, "unit"),
            precision=data.get("precision"),
            scale=_optional_translation(data, "scale"),
            value_format=data.get("valueFormat"),
            values=_values(data),
        )


@dataclass(frozen=True, kw_only=True)
class Attribute(ArrayItemDefinition):
    name: str
    source: str
    items: ArrayItemDefinition | None = None

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> Self:
        validate_semantic_rules({name: data})
        return cls(
            name=name,
            source=data["source"],
            type=AttributeType.from_dict(data),
            semantic_type=data["semanticType"],
            description=Translation.from_dict(data["description"]),
            nullable=data["nullable"],
            unit=_optional_translation(data, "unit"),
            precision=data.get("precision"),
            scale=_optional_translation(data, "scale"),
            value_format=data.get("valueFormat"),
            values=_values(data),
            items=ArrayItemDefinition.from_dict(data["items"])
            if "items" in data
            else None,
        )


def load_attributes(path: Path | None = None) -> Mapping[str, Attribute]:
    """Load packaged semantic attributes, or a semantic document at path."""
    data = (
        load_resource("semantic/attributes.json") if path is None else read_json(path)
    )
    validate_semantic_rules(data)
    return MappingProxyType(
        {name: Attribute.from_dict(name, entry) for name, entry in data.items()}
    )
