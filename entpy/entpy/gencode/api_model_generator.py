from entpy import (
    DatetimeField,
    EdgeField,
    JsonField,
    Pattern,
)
from entpy.framework.descriptor import Descriptor
from entpy.framework.fields.core import FieldWithDefault, FieldWithExample
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


def generate(descriptor: Descriptor, base_name: str) -> GeneratedContent:
    # Only use the fields for this specific descriptor. The patterns fields will
    # be handled by inheritance.
    fields = descriptor.get_sorted_fields()

    fields_code = ""
    types_imports = []
    type_checking_imports = []
    for field in fields:
        if field.is_internal:
            continue

        field_args = "None" if field.nullable else "..."
        if isinstance(field, FieldWithDefault):
            default = field.generate_default()
            if default:
                field_args = default

        if field.description:
            field_args += f", description={field.description!r}"
        if isinstance(field, FieldWithExample):
            default = field.get_example_as_string()
            if default:
                field_args += f", examples=[{default}]"

        quote = False
        if isinstance(field, DatetimeField):
            types_imports.append("from pydantic import AwareDatetime")
            python_type = "AwareDatetime"
        elif isinstance(field, EdgeField):
            edge_base = field.edge_class.__name__.removesuffix("Schema").removesuffix(
                "Pattern"
            )
            if edge_base != base_name:
                type_checking_imports.append(
                    f"from .{to_snake_case(edge_base)} import {edge_base}APIModel"
                )
            quote = True
            python_type = f"{edge_base}APIModel"
        elif isinstance(field, JsonField) and field.is_pydantic_field():
            # For Pydantic JsonFields, use the Pydantic model class directly
            pydantic_import = field.get_pydantic_model_import()
            if pydantic_import:
                types_imports.append(pydantic_import)
            python_type = field.get_entity_property_type()
        else:
            python_type = field.get_python_type()

        mapped_type = python_type + " | None" if field.nullable else python_type
        if quote:
            mapped_type = f'"{mapped_type}"'

        fields_code += (
            f"    {field.original_name}: {mapped_type} = APIField({field_args})\n"
        )

    extends = _generate_extends(descriptor=descriptor)

    return GeneratedContent(
        imports=[
            "from entpy.model import APIEntity",
            "from pydantic import Field as APIField",
        ]
        + types_imports
        + extends.imports,
        type_checking_imports=type_checking_imports,
        code=f"""
class {base_name}APIModel({extends.code}):
{fields_code or "    pass"}
""",
    )


def _generate_extends(descriptor: Descriptor) -> GeneratedContent:
    patterns = descriptor.get_patterns()
    code = ", ".join(
        [p.__class__.__name__.removesuffix("Pattern") + "APIModel" for p in patterns]
    )

    def get_import(pattern: Pattern) -> str:
        base_name = pattern.__class__.__name__.removesuffix("Pattern")
        return f"from .{to_snake_case(base_name)} import {base_name}APIModel"

    imports = [get_import(p) for p in patterns]
    return (
        GeneratedContent(code=code, imports=imports)
        if code
        else GeneratedContent(code="APIEntity")
    )
