from framework.ent_field import EntFieldWithDynamicExample, EntFieldWithExample
from framework.ent_schema import EntSchema
from gencode.generated_content import GeneratedContent


def generate(
    schema: EntSchema,
    base_name: str,
) -> GeneratedContent:
    # Separate nullable and non-nullable fields
    # We always process the mandatory fields first
    nullable_fields = [f for f in schema.get_fields() if f.nullable]
    non_nullable_fields = [f for f in schema.get_fields() if not f.nullable]

    # Build up the list of arguments the create function takes
    arguments_definition = ""
    for field in non_nullable_fields:
        arguments_definition += (
            f", {field.name}: {field.get_python_type()} | Sentinel = NOTHING"
        )
    for field in nullable_fields:
        arguments_definition += (
            f", {field.name}: {field.get_python_type()} | None = None"
        )

    # Build up the list of arguments the create function takes
    arguments_usage = "".join(
        [f", {field.name}={field.name}" for field in non_nullable_fields]
        + [f", {field.name}={field.name}" for field in nullable_fields]
    )

    # Build up the list of variables that will be passed to the mutator
    arguments_assignments = ""
    for field in non_nullable_fields + nullable_fields:
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
            {field.name} = generator()

"""

        # TODO check that mandatory fields have either an example or a dynamic example

    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
            "from framework.ent_field import EntField, EntFieldWithDynamicExample",
            "from sentinels import NOTHING, Sentinel  # type: ignore",
            f"from {schema.__class__.__module__} import {schema.__class__.__name__}",
        ],
        code=f"""
class {base_name}Example:
    @classmethod
    async def gen_create(
        cls, vc: ViewerContext{arguments_definition}
    ) -> {base_name}:
        # TODO make sure we only use this in test mode

{arguments_assignments}

        return await {base_name}Mutator.create(vc=vc{arguments_usage}).gen_savex()

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
