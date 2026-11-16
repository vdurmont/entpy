from dataclasses import dataclass
from enum import Enum
from importlib import import_module

from entpy import EdgeField, Field, Schema
from entpy.framework.descriptor import Descriptor
from entpy.framework.fields.bytes_field import BytesField
from entpy.framework.serialization import SerializationConfig
from entpy.gencode.utils import ImportedObject


@dataclass(frozen=True)
class SerializationContext:
    config: SerializationConfig
    tier_enum: ImportedObject

    @classmethod
    def load(cls, imported: ImportedObject) -> "SerializationContext":
        config = getattr(import_module(imported.module), imported.name)
        if not isinstance(config, SerializationConfig):
            raise TypeError(
                f"{imported.module}.{imported.name} must be a SerializationConfig, "
                + f"got {type(config)}"
            )
        enum = config.tier_enum
        return cls(
            config=config,
            tier_enum=ImportedObject(module=enum.__module__, name=enum.__name__),
        )


def _output_key(field: Field) -> str:
    if field.serialization is not None and field.serialization.name:
        return field.serialization.name
    return field.original_name


def _nested_tier(field: EdgeField, ctx: SerializationContext) -> Enum | None:
    if field.serialization is None:
        return None
    return (
        field.serialization.nested or ctx.config.tiers[field.serialization.tier].nested
    )


def validate_descriptor(
    descriptor: Descriptor, ctx: SerializationContext | None
) -> None:
    name = type(descriptor).__name__
    for field in descriptor.get_fields():
        serialization = field.serialization
        if serialization is None:
            continue
        label = f"{name}.{field.original_name}"
        if ctx is None:
            raise ValueError(
                f"{label} is serialized, but no serialization config was passed "
                + "to the generator."
            )
        if serialization.tier not in ctx.config.tiers:
            raise ValueError(
                f"{label} is serialized in {serialization.tier!r}, which is not "
                + f"a tier of {ctx.config.tier_enum.__name__}."
            )
        if isinstance(field, BytesField) and field.is_encrypted:
            raise ValueError(f"{label} is encrypted and cannot be serialized.")
        if isinstance(field, EdgeField):
            nested = _nested_tier(field, ctx)
            if nested is None:
                raise ValueError(
                    f"{label} is serialized in tier {serialization.tier.name}, "
                    + "which has no nested tier. Set one on the TierConfig or "
                    + "pass nested= to serialize()."
                )
            if nested not in ctx.config.tiers:
                raise ValueError(f"{label} nests at {nested!r}, which is not a tier.")
        elif serialization.nested is not None:
            raise ValueError(f"{label} is not an edge and cannot set nested=.")

    if isinstance(descriptor, Schema):
        keys = [_output_key(f) for f in descriptor.get_all_fields() if f.serialization]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(
                f"{name} serializes several fields under the same name: "
                + ", ".join(duplicates)
            )
