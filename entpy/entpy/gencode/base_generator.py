from entpy import DateField, EdgeField, IntervalField, Pattern, Schema, TimeField
from entpy.framework.descriptor import Descriptor
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import (
    ImportedObject,
    get_description,
    to_snake_case,
)


def generate(
    descriptor: Descriptor,
    base_name: str,
    vc: ImportedObject,
    privacy_mixin: ImportedObject | None = None,
) -> GeneratedContent:
    i = "I" if isinstance(descriptor, Pattern) else ""
    base_parent = None
    if isinstance(descriptor, Schema):
        base_parent = f"EntObjectBase[{vc.name}, {base_name}Model]"
    elif isinstance(descriptor, Pattern) and len(descriptor.get_patterns()) == 0:
        base_parent = f"EntPatternBase[{vc.name}, {base_name}Model]"
    extends_list = (
        ([privacy_mixin.name] if privacy_mixin else [])
        + [base_parent]
        + [
            f"I{pattern.__class__.__name__.removesuffix('Pattern')}"
            for pattern in descriptor.get_patterns()
        ]
    )
    extends = ",".join(list(filter(None, extends_list)))

    fields = _generate_fields(descriptor)
    edge_gens, edge_types = _generate_edge_gens(descriptor)

    unique_gens = _generate_unique_gens(
        descriptor=descriptor, base_name=base_name, vc=vc
    )

    imports = [
        "from functools import cache",
        "from entpy.framework.ent import "
        + ("EntPatternBase" if isinstance(descriptor, Pattern) else "EntObjectBase"),
    ]
    if privacy_mixin:
        imports.append(str(privacy_mixin))
    type_checking_imports = ["from entpy import Ent"]

    attributes = ""
    if isinstance(descriptor, Schema):
        attributes = "    schema = " + base_name + "Schema()"

    for pattern in descriptor.get_patterns():
        pattern_base_name = pattern.__class__.__name__.removesuffix("Pattern")
        class_name = f"I{pattern_base_name}"
        module_name = "." + to_snake_case(pattern_base_name)
        imports.append(f"from {module_name} import {class_name}")

    child_types = ""
    # Make the type checker happy for ents which implement multiple patterns
    if isinstance(descriptor, Schema) and len(descriptor.get_patterns()) > 1:
        child_types = f"""@classmethod
    def _get_child_type(  # type: ignore[override]
        cls,
        uuid_type: bytes,
    ) -> type[{base_name}]:
        raise NotImplementedError("get_child_type() should only be called on patterns")
    """

    return GeneratedContent(
        imports=imports + fields.imports + edge_gens.imports,
        type_checking_imports=type_checking_imports
        + fields.type_checking_imports
        + edge_gens.type_checking_imports,
        code=f"""
class {i}{base_name}({extends}):{get_description(descriptor)}
    m = {base_name}Model
{attributes}

    if TYPE_CHECKING:
{fields.code or "        pass"}

{unique_gens}

{edge_gens.code}

    @classmethod
    @cache
    def _get_edge_type(cls, edge_name: str) -> tuple[type[Ent], bool]:
{edge_types.code}
        return super()._get_edge_type(edge_name)

    {child_types}

    @classmethod
    def query(  {"# type: ignore[override]" if descriptor.get_patterns() else ""}
        cls,
        vc: {vc.name},
    ) -> {i}{base_name}Query:
        return {i}{base_name}Query(vc=vc)
""",
    )


def _generate_fields(schema: Descriptor) -> GeneratedContent:
    fields = schema.get_all_fields()
    field_code = ""
    imports = ["from typing import Any, TYPE_CHECKING"]

    for field in fields:
        if isinstance(field, DateField):
            imports.append("from datetime import date")
        if isinstance(field, TimeField):
            imports.append("from datetime import time")
        if isinstance(field, IntervalField):
            imports.append("from datetime import timedelta")
        accessor_type = field.get_python_type() + (" | None" if field.nullable else "")
        field_code += f"        {field.name}: {accessor_type}\n"
        if field.description:
            field_code += f"""        \"\"\"
        {field.description}
        \"\"\"\n"""

    return GeneratedContent(
        imports=imports,
        code=field_code,
    )


def _generate_edge_gens(
    schema: Descriptor,
) -> tuple[GeneratedContent, GeneratedContent]:
    fields = schema.get_sorted_fields()
    type_stubs = ""
    edge_types = ""
    type_checking_imports = []

    for field in fields:
        # If the field is an edge, we want to generate a utility function to
        # load the edge directly
        if isinstance(field, EdgeField):
            load = ""
            if field.edge_class != schema.__class__:
                module = "." + to_snake_case(
                    field.edge_class.__name__.removesuffix("Schema").removesuffix(
                        "Pattern"
                    )
                )
                # We import the edge type locally to avoid circular imports
                type_checking_imports.append(
                    f"from {module} import {field.get_edge_type()}"
                )
                load = f"from {module} import {field.get_edge_type()}\n        "
            type_stubs += f"""
        async def gen_{field.original_name}(self) -> "{field.get_edge_type()}"{" | None" if field.nullable else ""}:
            pass

"""  # noqa: E501

            edge_types += f'            case "{field.original_name}":\n'
            edge_types += f"                {load}\n"
            edge_types += (
                f"                return ({field.get_edge_type()}, {field.nullable})\n"
            )

    return (
        GeneratedContent(
            type_checking_imports=type_checking_imports,
            code=type_stubs,
        ),
        GeneratedContent(
            code=f"        match edge_name:\n{edge_types}" if edge_types else "",
        ),
    )


def _generate_unique_gens(
    descriptor: Descriptor, base_name: str, vc: ImportedObject
) -> str:
    unique_gens = ""
    for field in descriptor.get_sorted_fields():
        if field.is_unique:
            unique_gens += f"""
        @classmethod
        async def gen_from_{field.name}(cls, vc: {vc.name}, {field.name}: {field.get_python_type()}, for_update: bool = False) -> Self | None:
            pass

        @classmethod
        async def genx_from_{field.name}(cls, vc: {vc.name}, {field.name}: {field.get_python_type()}, for_update: bool = False) -> Self:
            pass

        @classmethod
        async def genx_or_404_from_{field.name}(cls, vc: {vc.name}, {field.name}: {field.get_python_type()}, for_update: bool = False) -> Self:
            pass
"""  # noqa: E501
    return unique_gens
