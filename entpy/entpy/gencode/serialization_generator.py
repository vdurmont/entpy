from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from importlib import import_module

from entpy import (
    ComputedField,
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
from entpy.framework.imported_object import ImportedObject
from entpy.framework.serialization import SerializationConfig
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


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

    def tier_ref(self, tier: Enum) -> str:
        return f"{self.tier_enum.name}.{tier.name}"


Member = Field | ComputedField
type Node = tuple[type[Schema], Enum]


def base_name_of(descriptor_class: type[Descriptor]) -> str:
    return descriptor_class.__name__.removesuffix("Schema").removesuffix("Pattern")


def api_model_name(base_name: str, tier: Enum) -> str:
    suffix = "".join(part.capitalize() for part in tier.name.lower().split("_"))
    return f"{base_name}{suffix}APIModel"


def api_model_names(base_name: str, ctx: SerializationContext) -> list[str]:
    return [api_model_name(base_name, tier) for tier in ctx.config.get_ordered_tiers()]


def get_all_computed_fields(descriptor: Descriptor) -> list[ComputedField]:
    fields = list(descriptor.get_computed_fields())
    for pattern in descriptor.get_patterns():
        fields += get_all_computed_fields(pattern)
    return fields


def _own_members(descriptor: Descriptor) -> list[Member]:
    fields: list[Member] = [
        f for f in descriptor.get_sorted_fields() if not f.is_deprecated
    ]
    return fields + list(descriptor.get_computed_fields())


def _all_members(descriptor: Descriptor) -> list[Member]:
    fields: list[Member] = list(descriptor.get_all_fields())
    return fields + get_all_computed_fields(descriptor)


def exposes_fields(descriptor: Descriptor) -> bool:
    return any(m.serialization is not None for m in _all_members(descriptor))


def _output_key(member: Member) -> str:
    if member.serialization is not None and member.serialization.name:
        return member.serialization.name
    if isinstance(member, Field):
        return member.original_name
    return member.name


def _nested_tier(field: EdgeField, ctx: SerializationContext) -> Enum:
    serialization = field.serialization
    if serialization is None:
        raise ValueError(f"Edge {field.original_name} is not serialized.")
    nested = serialization.nested or ctx.config.tiers[serialization.tier].nested
    if nested is None:
        raise ValueError(
            f"Edge {field.original_name} is serialized in tier "
            + f"{serialization.tier.name}, which has no nested tier. Set one on "
            + "the TierConfig or pass nested= to serialize()."
        )
    return nested


def validate_descriptor(
    descriptor: Descriptor, ctx: SerializationContext | None
) -> None:
    name = type(descriptor).__name__
    members = _own_members(descriptor)
    for member in members:
        label = f"{name}.{member.name}"
        if isinstance(member, ComputedField) and member.serialization is None:
            raise ValueError(f"Computed field {label} must call serialize().")
        serialization = member.serialization
        if serialization is None:
            continue
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
        if isinstance(member, ComputedField):
            continue
        if member.is_internal:
            raise ValueError(f"{label} is internal and cannot be serialized.")
        if isinstance(member, BytesField) and member.is_encrypted:
            raise ValueError(f"{label} is encrypted and cannot be serialized.")
        if isinstance(member, EdgeField):
            nested = _nested_tier(member, ctx)
            if nested not in ctx.config.tiers:
                raise ValueError(f"{label} nests at {nested!r}, which is not a tier.")
            if not exposes_fields(member.edge_class()):
                raise ValueError(
                    f"{label} is serialized, but {member.edge_class.__name__} "
                    + "exposes no fields."
                )
        elif serialization.nested is not None:
            raise ValueError(f"{label} is not an edge and cannot set nested=.")

    if isinstance(descriptor, Schema):
        keys = [_output_key(m) for m in _all_members(descriptor) if m.serialization]
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
    if isinstance(field, DatetimeField):
        python_type = "AwareDatetime"
        imports = ["from pydantic import AwareDatetime"]
        type_checking_imports = []
    elif isinstance(field, EdgeField):
        target_base = base_name_of(field.edge_class)
        target_model = api_model_name(target_base, _nested_tier(field, ctx))
        python_type = f"SerializeAsAny[{target_model}]"
        imports = ["from pydantic import SerializeAsAny"]
        type_checking_imports = [
            f"from .{to_snake_case(target_base)} import {target_model}"
        ]
    else:
        python_type = field.get_python_type()
        imports = []
        type_checking_imports = []
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
    members = [m for m in _own_members(descriptor) if m.serialization is not None]

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
            bases.append("TieredAPIEntity")
            imports.append("from entpy.model import TieredAPIEntity")

        fields_code = ""
        for member in members:
            if member.serialization is None or member.serialization.tier != tier:
                continue
            if isinstance(member, ComputedField):
                python_type = member.python_type
            else:
                generated_type = _python_type(member, ctx)
                python_type = generated_type.code
                imports += generated_type.imports
                type_checking_imports += generated_type.type_checking_imports
            args = "..."
            if member.description:
                args += f", description={member.description!r}"
            fields_code += (
                f"    {_output_key(member)}: {python_type} = APIField({args})\n"
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


def _generate_overloads(
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
        self, tier: Literal[{ctx.tier_ref(tier)}]
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
    signature = _generate_overloads(base_name, ctx, abstract=True)
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
    members = [m for m in _all_members(schema) if m.serialization is not None]
    blocks = ""
    for tier in ctx.config.get_ordered_tiers():
        lines = ""
        for member in members:
            if member.serialization is None or member.serialization.tier != tier:
                continue
            key = _output_key(member)
            if isinstance(member, ComputedField):
                resolver = member.resolver
                lines += f"            {resolver}\n"
                lines += f'            values["{key}"] = await {resolver.name}(self)\n'
            elif isinstance(member, EdgeField):
                variable = f"edge_{member.original_name}"
                nested = ctx.tier_ref(_nested_tier(member, ctx))
                serialize = f"await {variable}.gen_serialize({nested})"
                lines += f"            {variable} = await self.gen_{member.original_name}()\n"
                if member.nullable:
                    serialize = f"None if {variable} is None else {serialize}"
                lines += f'            values["{key}"] = {serialize}\n'
            else:
                lines += f'            values["{key}"] = self.{member.name}\n'
        if lines:
            including = ", ".join(
                ctx.tier_ref(t) for t in ctx.config.get_tiers_including(tier)
            )
            blocks += f"        if tier in ({including},):\n{lines}"

    models_by_tier = ", ".join(
        f"{ctx.tier_ref(tier)}: {api_model_name(base_name, tier)}"
        for tier in ctx.config.get_ordered_tiers()
    )
    signature = _generate_overloads(base_name, ctx, abstract=False)
    tier_type = ctx.tier_enum.name
    base_model = api_model_name(base_name, ctx.config.get_ordered_tiers()[0])
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
    annotation_types = sorted(
        set(_ANNOTATION_TYPES + enum_types), key=lambda t: (t.module, t.name)
    )
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
