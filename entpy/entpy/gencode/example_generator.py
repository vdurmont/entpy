from entpy import EdgeField, Schema
from entpy.framework.fields.core import (
    FieldWithDynamicExample,
    FieldWithExample,
)
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


def generate(schema: Schema, base_name: str, vc_name: str) -> GeneratedContent:
    # Build up the list of arguments the gen_create function takes
    arguments_definition = ""
    for field in schema.get_all_fields():
        typehint = field.get_python_type()
        typehint += " | None = None" if field.nullable else " | Sentinel = NOTHING"
        arguments_definition += f", {field.name}: {typehint}"

    # Build up the list of variables that will be passed to the mutator
    arguments_assignments = ""
    for field in schema.get_all_fields():
        if isinstance(field, FieldWithExample):
            example = field.get_example_as_string()
            if example:
                arguments_assignments += (
                    "        "
                    + field.name
                    + " = "
                    + example
                    + f" if isinstance({field.name}, Sentinel) else {field.name}\n\n"
                )
        if isinstance(field, FieldWithDynamicExample):
            generator = field.get_example_generator()
            if generator:
                arguments_assignments += f"""
        if isinstance({field.name}, Sentinel):
            field = _get_field("{field.name}")
            if not isinstance(field, FieldWithDynamicExample):
                raise TypeError("Internal ent error: "+f"field {{field.name}} must support dynamic examples.")
            generator = field.get_example_generator()
            if generator:
                {field.name} = generator()

"""  # noqa: E501

        if isinstance(field, EdgeField) and field.should_generate_example:
            edge_base_name = field.edge_class.__name__.replace("Schema", "").replace(
                "Pattern", ""
            )
            i = "I" if field.edge_class.__name__.endswith("Pattern") else ""
            # We skip examples for edges that point to the same schema or a pattern
            # implemented by the current Ent to avoid recursive creations. The
            # developpers can manually add those edges if they want.
            if edge_base_name != base_name and field.edge_class.__name__ not in [
                p.__class__.__name__ for p in schema.get_patterns()
            ]:
                # We also import the example class locally to avoid circular imports
                edge_filename = to_snake_case(edge_base_name)
                arguments_assignments += f"""
        if isinstance({field.name}, Sentinel) or {field.name} is None:
            from .{edge_filename} import {i}{edge_base_name}Example
            {field.name}_ent = await {i}{edge_base_name}Example.gen_create(vc)
            {field.name} = {field.name}_ent.id
"""

        # TODO check that mandatory fields have either an example or a dynamic example

    # Build up the list of arguments the Mutator.create function takes
    mutator_arguments = "\n".join(
        [f", {field.name}={field.name}" for field in schema.get_all_fields()]
    )

    return GeneratedContent(
        imports=[
            "from entpy import Field, FieldWithDynamicExample",
            "from sentinels import NOTHING, Sentinel  # type: ignore",
            f"from {schema.__class__.__module__} import {schema.__class__.__name__}",
        ],
        code=f"""
class {base_name}Example:
    @classmethod
    async def gen_create(
        cls, vc: {vc_name}, created_at: datetime | None = None{arguments_definition}
    ) -> {base_name}:
        # TODO make sure we only use this in test mode

{arguments_assignments}

        return await {base_name}Mutator.create(vc=vc, created_at=created_at{mutator_arguments}).gen_savex()
""",  # noqa: E501
    )
