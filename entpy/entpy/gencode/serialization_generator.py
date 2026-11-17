from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from importlib import import_module

from entpy import (
    DateField,
    DatetimeField,
    EdgeField,
    EnumField,
    Field,
    IntervalField,
    Pattern,
    Schema,
    TimeField,
)
from entpy.framework.descriptor import Descriptor
from entpy.framework.fields.bytes_field import BytesField
from entpy.framework.serialization import SerializationConfig
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import ImportedObject, to_snake_case


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


type Node = tuple[type[Schema], Enum]


def base_name_of(descriptor_class: type[Descriptor]) -> str:
    return descriptor_class.__name__.removesuffix("Schema").removesuffix("Pattern")


def api_model_name(base_name: str, tier: Enum) -> str:
    suffix = "".join(part.capitalize() for part in tier.name.lower().split("_"))
    return f"{base_name}{suffix}APIModel"


def api_model_names(base_name: str, ctx: SerializationContext) -> list[str]:
    return [api_model_name(base_name, tier) for tier in ctx.config.get_ordered_tiers()]


def exposes_fields(descriptor: Descriptor) -> bool:
    return any(field.serialization for field in descriptor.get_all_fields())


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
            if not exposes_fields(field.edge_class()):
                raise ValueError(
                    f"{label} is serialized, but {field.edge_class.__name__} "
                    + "exposes no fields."
                )
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


def validate_no_cycles(
    schema_classes: list[type[Schema]],
    get_children: Callable[[type[Pattern]], list[type[Schema]]],
    ctx: SerializationContext,
) -> None:
    def get_targets(node: Node) -> list[tuple[str, Node]]:
        schema_class, tier = node
        chain = ctx.config.get_chain(tier)
        targets = []
        for field in schema_class().get_all_fields():
            if not isinstance(field, EdgeField) or field.serialization is None:
                continue
            if field.serialization.tier not in chain:
                continue
            nested = _nested_tier(field, ctx)
            if nested is None:
                raise ValueError(f"Edge {field.original_name} has no nested tier.")
            edge_class = field.edge_class
            if issubclass(edge_class, Pattern):
                target_classes = get_children(edge_class)
            elif issubclass(edge_class, Schema):
                target_classes = [edge_class]
            else:
                raise TypeError(f"Unknown edge target: {edge_class}")
            for target_class in target_classes:
                targets.append((field.original_name, (target_class, nested)))
        return targets

    def describe(node: Node) -> str:
        return f"{base_name_of(node[0])}[{node[1].name}]"

    done: set[Node] = set()

    def visit(node: Node, path: list[str], on_path: list[Node]) -> None:
        if node in on_path:
            start = on_path.index(node)
            cycle = " -> ".join(path[start * 2 :] + [describe(node)])
            raise ValueError(f"Serialization nests in a cycle: {cycle}")
        if node in done:
            return
        for edge_name, target in get_targets(node):
            visit(target, path + [describe(node), edge_name], on_path + [node])
        done.add(node)

    for schema_class in schema_classes:
        for tier in ctx.config.get_ordered_tiers():
            visit((schema_class, tier), [], [])


def _python_type(field: Field, ctx: SerializationContext) -> GeneratedContent:
    imports: list[str] = []
    type_checking_imports: list[str] = []
    if isinstance(field, DatetimeField):
        python_type = "AwareDatetime"
        imports.append("from pydantic import AwareDatetime")
    elif isinstance(field, EdgeField):
        nested = _nested_tier(field, ctx)
        if nested is None:
            raise ValueError(f"Edge {field.original_name} has no nested tier.")
        target_base = base_name_of(field.edge_class)
        target_model = api_model_name(target_base, nested)
        python_type = f"SerializeAsAny[{target_model}]"
        imports.append("from pydantic import SerializeAsAny")
        type_checking_imports.append(
            f"from .{to_snake_case(target_base)} import {target_model}"
        )
    else:
        python_type = field.get_python_type()
        if isinstance(field, EnumField):
            enum_class = field.enum_class
            imports.append(f"from {enum_class.__module__} import {enum_class.__name__}")
        elif isinstance(field, DateField):
            imports.append("from datetime import date")
        elif isinstance(field, TimeField):
            imports.append("from datetime import time")
        elif isinstance(field, IntervalField):
            imports.append("from datetime import timedelta")
    if field.nullable:
        python_type += " | None"
    return GeneratedContent(
        code=python_type, imports=imports, type_checking_imports=type_checking_imports
    )


def generate_api_models(
    descriptor: Descriptor, base_name: str, ctx: SerializationContext
) -> GeneratedContent:
    if not exposes_fields(descriptor):
        return GeneratedContent(code="")
    imports = ["from pydantic import Field as APIField"]
    type_checking_imports: list[str] = []
    code = ""
    fields = [
        f
        for f in descriptor.get_sorted_fields()
        if f.serialization is not None and not f.is_deprecated
    ]

    for tier in ctx.config.get_ordered_tiers():
        bases = []
        included = ctx.config.tiers[tier].includes
        if included is not None:
            bases.append(api_model_name(base_name, included))
        for pattern in descriptor.get_patterns():
            if not exposes_fields(pattern):
                continue
            pattern_base = base_name_of(type(pattern))
            pattern_model = api_model_name(pattern_base, tier)
            bases.append(pattern_model)
            imports.append(
                f"from .{to_snake_case(pattern_base)} import {pattern_model}"
            )
        if not bases:
            bases.append("APIEntity")
            imports.append("from entpy.model import APIEntity")

        fields_code = ""
        for field in fields:
            if field.serialization is None or field.serialization.tier != tier:
                continue
            python_type = _python_type(field, ctx)
            imports += python_type.imports
            type_checking_imports += python_type.type_checking_imports
            args = "..."
            if field.description:
                args += f", description={field.description!r}"
            fields_code += (
                f"    {_output_key(field)}: {python_type.code} = APIField({args})\n"
            )

        code += f"""

class {api_model_name(base_name, tier)}({", ".join(bases)}):
{fields_code or "    pass"}
"""

    own_module = f"from .{to_snake_case(base_name)} import "
    type_checking_imports = [
        i for i in type_checking_imports if not i.startswith(own_module)
    ]
    return GeneratedContent(
        code=code, imports=imports, type_checking_imports=type_checking_imports
    )


def _tier_ref(ctx: SerializationContext, tier: Enum) -> str:
    return f"{ctx.tier_enum.name}.{tier.name}"


def _generate_signature(
    base_name: str, ctx: SerializationContext, abstract: bool
) -> str:
    tiers = ctx.config.get_ordered_tiers()
    tier_type = ctx.tier_enum.name
    base_model = api_model_name(base_name, tiers[0])
    overloads = ""
    if len(tiers) > 1:
        for tier in tiers:
            overloads += f"""
    @overload
    async def gen_serialize(
        self, tier: Literal[{_tier_ref(ctx, tier)}]
    ) -> {api_model_name(base_name, tier)}: ...
"""
        overloads += f"""
    @overload
    async def gen_serialize(self, tier: {tier_type}) -> {base_model}: ...
"""
    decorator = "\n    @abstractmethod" if abstract else ""
    return f"""{overloads}{decorator}
    async def gen_serialize(self, tier: {tier_type}) -> {base_model}:"""


def generate_pattern_serialize(
    pattern: Pattern, base_name: str, ctx: SerializationContext
) -> GeneratedContent:
    if not exposes_fields(pattern):
        return GeneratedContent(code="")
    signature = _generate_signature(base_name, ctx, abstract=True)
    return GeneratedContent(
        code=f"{signature}\n        pass\n",
        imports=[
            "from abc import abstractmethod",
            "from typing import Literal, overload",
            str(ctx.tier_enum),
        ],
    )


def generate_schema_serialize(
    schema: Schema, base_name: str, ctx: SerializationContext
) -> GeneratedContent:
    if not exposes_fields(schema):
        return GeneratedContent(code="")
    fields = [f for f in schema.get_all_fields() if f.serialization is not None]
    tiers = ctx.config.get_ordered_tiers()
    blocks = ""
    for tier in tiers:
        lines = ""
        for field in fields:
            if field.serialization is None or field.serialization.tier != tier:
                continue
            key = _output_key(field)
            if isinstance(field, EdgeField):
                nested = _nested_tier(field, ctx)
                if nested is None:
                    raise ValueError(f"Edge {field.original_name} has no nested tier.")
                variable = f"edge_{field.original_name}"
                value = f"await {variable}.gen_serialize({_tier_ref(ctx, nested)})"
                if field.nullable:
                    value = f"None if {variable} is None else {value}"
                lines += (
                    f"            {variable} = await self.gen_{field.original_name}()\n"
                )
                lines += f'            values["{key}"] = {value}\n'
            else:
                lines += f'            values["{key}"] = self.{field.name}\n'
        if lines:
            including = ", ".join(
                _tier_ref(ctx, t) for t in tiers if tier in ctx.config.get_chain(t)
            )
            blocks += f"        if tier in ({including},):\n{lines}"

    tier_type = ctx.tier_enum.name
    base_model = api_model_name(base_name, tiers[0])
    models_by_tier = ", ".join(
        f"{_tier_ref(ctx, tier)}: {api_model_name(base_name, tier)}" for tier in tiers
    )
    signature = _generate_signature(base_name, ctx, abstract=False)
    code = f"""{signature}
        from .all_models import ensure_api_models_built

        ensure_api_models_built()
        values: dict[str, Any] = {{
            "id": self.id,
            "entity_type": "{base_name}",
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "soft_deleted_at": self.soft_deleted_at,
        }}
{blocks}
        api_models: dict[{tier_type}, type[{base_model}]] = {{{models_by_tier}}}
        return api_models[tier].model_validate(values)
"""
    return GeneratedContent(
        code=code,
        imports=["from typing import Any, Literal, overload", str(ctx.tier_enum)],
    )


_ANNOTATION_TYPES = [
    ImportedObject(module="datetime", name="date"),
    ImportedObject(module="datetime", name="time"),
    ImportedObject(module="datetime", name="timedelta"),
    ImportedObject(module="pydantic", name="AwareDatetime"),
    ImportedObject(module="pydantic", name="SerializeAsAny"),
    ImportedObject(module="typing", name="Any"),
    ImportedObject(module="uuid", name="UUID"),
]


def get_serialized_enum_types(descriptor: Descriptor) -> list[ImportedObject]:
    return [
        ImportedObject(
            module=field.enum_class.__module__, name=field.enum_class.__name__
        )
        for field in descriptor.get_fields()
        if isinstance(field, EnumField) and field.serialization is not None
    ]


def generate_ensure_built(
    api_model_imports: list[tuple[str, str]],
    enum_types: list[ImportedObject],
) -> GeneratedContent:
    # Pydantic resolves an inherited annotation in the subclass's module, which
    # need not import the types the parent's fields use. The rebuild namespace
    # carries every one of them.
    unique_types = {(t.module, t.name): t for t in _ANNOTATION_TYPES + enum_types}
    annotation_types = [unique_types[key] for key in sorted(unique_types)]
    names = [t.name for t in annotation_types]
    clashes = sorted({name for name in names if names.count(name) > 1})
    if clashes:
        raise ValueError(
            "Serialized fields use different types with the same name: "
            + ", ".join(clashes)
        )
    models = "".join(f"    {model},\n" for _, model in api_model_imports)
    types = "".join(f'    "{t.name}": {t.name},\n' for t in annotation_types)
    return GeneratedContent(
        imports=["from functools import cache", "from pydantic import BaseModel"]
        + [str(t) for t in annotation_types]
        + [f"from .{module} import {model}" for module, model in api_model_imports],
        code=f"""

_API_MODELS: list[type[BaseModel]] = [
{models}]

_ANNOTATION_TYPES: dict[str, object] = {{
{types}}}


@cache
def ensure_api_models_built() -> None:
    namespace = {{
        **_ANNOTATION_TYPES,
        **{{model.__name__: model for model in _API_MODELS}},
    }}
    for model in _API_MODELS:
        model.model_rebuild(_types_namespace=namespace)
""",
    )
