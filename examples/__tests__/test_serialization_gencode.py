from enum import Enum

import pytest

from entpy import (
    Action,
    AllowAll,
    BytesField,
    EdgeDelegate,
    EdgeField,
    Field,
    PrivacyRule,
    Schema,
    SerializationConfig,
    StringField,
    TierConfig,
)
from entpy.gencode.serialization_generator import (
    SerializationContext,
    validate_descriptor,
)
from entpy.gencode.utils import ImportedObject


class Level(Enum):
    LOW = "LOW"
    HIGH = "HIGH"


class Three(Enum):
    BASE = "BASE"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Other(Enum):
    LOW = "LOW"


CTX = SerializationContext(
    config=SerializationConfig(
        tiers={
            Level.LOW: TierConfig(),
            Level.HIGH: TierConfig(includes=Level.LOW, nested=Level.LOW),
        },
    ),
    tier_enum=ImportedObject(module=__name__, name="Level"),
)


class _Base(Schema):
    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]


class TargetSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [StringField("name", 10).serialize(Level.LOW)]


class ValidSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [
            StringField("label", 10).serialize(Level.LOW, name="title"),
            StringField("hidden", 10),
            EdgeField("target", TargetSchema).serialize(Level.HIGH),
            EdgeField("pinned", TargetSchema).serialize(Level.LOW, nested=Level.LOW),
        ]


class ForeignTierSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [StringField("name", 10).serialize(Other.LOW)]


class EncryptedSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [BytesField("secret").encrypt().serialize(Level.HIGH)]


class NestedOnScalarSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [StringField("name", 10).serialize(Level.LOW, nested=Level.LOW)]


class EdgeWithoutNestingSchema(_Base):
    def get_fields(self) -> list[Field]:
        return [EdgeField("target", TargetSchema).serialize(Level.LOW)]


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
        SerializationConfig(tiers={Level.LOW: TierConfig(), Level.HIGH: TierConfig()})


def test_config_requires_every_enum_member() -> None:
    with pytest.raises(ValueError, match="missing: HIGH"):
        SerializationConfig(tiers={Level.LOW: TierConfig()})


def test_config_rejects_include_cycles() -> None:
    with pytest.raises(ValueError, match="cycle"):
        SerializationConfig(
            tiers={
                Three.BASE: TierConfig(),
                Three.LEFT: TierConfig(includes=Three.RIGHT),
                Three.RIGHT: TierConfig(includes=Three.LEFT),
            },
        )


def test_config_orders_a_tier_after_the_tiers_it_includes() -> None:
    config = SerializationConfig(
        tiers={
            Three.RIGHT: TierConfig(includes=Three.LEFT),
            Three.BASE: TierConfig(),
            Three.LEFT: TierConfig(includes=Three.BASE),
        },
    )

    assert config.get_chain(Three.RIGHT) == [Three.BASE, Three.LEFT, Three.RIGHT]


def test_valid_declarations_pass() -> None:
    validate_descriptor(ValidSchema(), CTX)


def test_serialized_field_without_config_is_rejected() -> None:
    with pytest.raises(ValueError, match="no serialization config"):
        validate_descriptor(TargetSchema(), None)


def test_tier_from_another_enum_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a tier of Level"):
        validate_descriptor(ForeignTierSchema(), CTX)


def test_encrypted_field_cannot_be_serialized() -> None:
    with pytest.raises(ValueError, match="encrypted"):
        validate_descriptor(EncryptedSchema(), CTX)


def test_nested_is_only_for_edges() -> None:
    with pytest.raises(ValueError, match="not an edge"):
        validate_descriptor(NestedOnScalarSchema(), CTX)


def test_edge_needs_a_nested_tier() -> None:
    with pytest.raises(ValueError, match="no nested tier"):
        validate_descriptor(EdgeWithoutNestingSchema(), CTX)


def test_output_keys_must_be_unique() -> None:
    with pytest.raises(ValueError, match="same name: label"):
        validate_descriptor(DuplicateKeySchema(), CTX)


def test_edge_to_an_ent_exposing_no_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="SilentSchema exposes no fields"):
        validate_descriptor(PointsAtSilentSchema(), CTX)
