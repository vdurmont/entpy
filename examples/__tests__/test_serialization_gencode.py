from enum import Enum

import pytest

from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
    EdgeField,
    Field,
    PrivacyRule,
    Schema,
    SerializationConfig,
    StringField,
    TierConfig,
)
from entpy.framework.imported_object import ImportedObject
from entpy.gencode.serialization_generator import (
    SerializationContext,
    validate_descriptor,
    validate_no_cycles,
)


class Level(Enum):
    LOW = "LOW"
    HIGH = "HIGH"


CONFIG = SerializationConfig(
    tiers={
        Level.LOW: TierConfig(),
        Level.HIGH: TierConfig(includes=Level.LOW, nested=Level.LOW),
    },
)
CTX = SerializationContext(
    config=CONFIG, tier_enum=ImportedObject(module=__name__, name="Level")
)


class _Base(Schema):
    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]


class CycleASchema(_Base):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("b", CycleBSchema).serialize(Level.LOW, nested=Level.LOW),
        ]


class CycleBSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("a", CycleASchema).serialize(Level.LOW, nested=Level.LOW),
        ]


class InternalSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [StringField("secret", 10).internal().serialize(Level.HIGH)]


class NestedOnScalarSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [StringField("name", 10).serialize(Level.LOW, nested=Level.LOW)]


class EdgeWithoutNestingSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [EdgeField("other", CycleASchema).serialize(Level.LOW)]


class SilentSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [StringField("name", 10)]


class PointsAtSilentSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [EdgeField("silent", SilentSchema).serialize(Level.HIGH)]


class DuplicateKeySchema(_Base):
    def get_fields(self) -> list[Field]:
        return [
            StringField("first", 10).serialize(Level.LOW, name="label"),
            StringField("second", 10).serialize(Level.LOW, name="label"),
        ]


def test_config_requires_a_single_chain() -> None:
    with pytest.raises(ValueError, match="single chain"):
        SerializationConfig(
            tiers={Level.LOW: TierConfig(), Level.HIGH: TierConfig()},
        )


def test_config_requires_every_enum_member() -> None:
    with pytest.raises(ValueError, match="missing: HIGH"):
        SerializationConfig(tiers={Level.LOW: TierConfig()})


class Three(Enum):
    BASE = "BASE"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


def test_config_rejects_include_cycles() -> None:
    with pytest.raises(ValueError, match="cycle"):
        SerializationConfig(
            tiers={
                Three.BASE: TierConfig(),
                Three.LEFT: TierConfig(includes=Three.RIGHT),
                Three.RIGHT: TierConfig(includes=Three.LEFT),
            },
        )


def test_serialized_field_without_config_is_rejected() -> None:
    with pytest.raises(ValueError, match="no serialization config"):
        validate_descriptor(NestedOnScalarSchema(), None)


def test_internal_field_cannot_be_serialized() -> None:
    with pytest.raises(ValueError, match="internal"):
        validate_descriptor(InternalSchema(), CTX)


def test_nested_is_only_for_edges() -> None:
    with pytest.raises(ValueError, match="not an edge"):
        validate_descriptor(NestedOnScalarSchema(), CTX)


def test_edge_needs_a_nested_tier() -> None:
    with pytest.raises(ValueError, match="no nested tier"):
        validate_descriptor(EdgeWithoutNestingSchema(), CTX)


def test_output_keys_must_be_unique() -> None:
    with pytest.raises(ValueError, match="same name: label"):
        validate_descriptor(DuplicateKeySchema(), CTX)


def test_nesting_cycles_are_rejected() -> None:
    with pytest.raises(
        ValueError, match=r"CycleA\[LOW\] -> b -> CycleB\[LOW\] -> a -> CycleA\[LOW\]"
    ):
        validate_no_cycles(
            schema_classes=[CycleASchema, CycleBSchema],
            get_children=lambda _pattern: [],
            ctx=CTX,
        )


def test_edge_to_an_ent_exposing_no_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="SilentSchema exposes no fields"):
        validate_descriptor(PointsAtSilentSchema(), CTX)
