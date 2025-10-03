from framework.ent_field import (
    EdgeField,
    EntFieldWithDynamicExample,
    EntFieldWithExample,
)
from framework.ent_schema import EntSchema
from gencode.generated_content import GeneratedContent
from gencode.utils import to_snake_case


def generate(
    schema: EntSchema,
    base_name: str,
) -> GeneratedContent:
    # Build up the list of arguments the gen_create function takes
    arguments_definition = ""
    for field in schema.get_sorted_fields():
        typehint = field.get_python_type()
        typehint += " | None = None" if field.nullable else " | Sentinel = NOTHING"
        arguments_definition += f", {field.name}: {typehint}"

    # Build up the list of variables that will be passed to the mutator
    arguments_assignments = ""
    edges_imports = []
    for field in schema.get_sorted_fields():
        if isinstance(field, EntFieldWithExample):
            example = field.get_example_as_string()
            if example:
                arguments_assignments += (
                    "        "
                    + field.name
                    + " = "
                    + example
                    + f" if isinstance({field.name}, Sentinel) else {field.name}\n\n"
                )
        if isinstance(field, EntFieldWithDynamicExample):
            generator = field.get_example_generator()
            if generator:
                arguments_assignments += f"""
        if isinstance({field.name}, Sentinel):
            field = cls._get_field("{field.name}")
            if not isinstance(field, EntFieldWithDynamicExample):
                raise TypeError("Internal ent error: "+f"field {{field.name}} must support dynamic examples.")
            generator = field.get_example_generator()
            if generator:
                {field.name} = generator()

"""  # noqa: E501

        if isinstance(field, EdgeField) and field.should_generate_example:
            edge_base_name = field.edge_class.__name__.replace("Schema", "")
            edge_filename = to_snake_case(edge_base_name)
            edges_imports.append(
                f"from .{edge_filename} import {edge_base_name}Example"
            )
            arguments_assignments += f"""
        {field.name}_ent = await {edge_base_name}Example.gen_create(vc)
        {field.name} = {field.name}_ent.id
"""

        # TODO check that mandatory fields have either an example or a dynamic example

    # Build up the list of arguments the Mutator.create function takes
    mutator_arguments = "\n".join(
        [f", {field.name}={field.name}" for field in schema.get_sorted_fields()]
    )

    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
            "from framework.ent_field import EntField, EntFieldWithDynamicExample",
            "from sentinels import NOTHING, Sentinel  # type: ignore",
            f"from {schema.__class__.__module__} import {schema.__class__.__name__}",
        ]
        + edges_imports,
        code=f"""
class {base_name}Example:
    @classmethod
    async def gen_create(
        cls, vc: ViewerContext{arguments_definition}
    ) -> {base_name}:
        # TODO make sure we only use this in test mode

{arguments_assignments}

        return await {base_name}Mutator.create(vc=vc{mutator_arguments}).gen_savex()

    @classmethod
    def _get_field(cls, field_name: str) -> EntField:
        schema = {base_name}Schema()
        fields = schema.get_fields()
        field = list(
            filter(
                lambda field: field.name == field_name,
                fields,
            )
        )[0]
        if not field:
            raise ValueError(f"Unknown field: {{field_name}}")
        return field
""",
    )
