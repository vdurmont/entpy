from framework.ent_field import EntFieldWithExample
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
            if field.has_example():
                arguments_assignments += (
                    "        "
                    + field.name
                    + " = "
                    + field.get_example_as_string()
                    + f" if isinstance({field.name}, Sentinel) else {field.name}\n"
                )
            elif not field.nullable:
                raise ValueError(
                    f"In {base_name}, mandatory field '{field.name}' must have an example."
                )

    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
            "from sentinels import NOTHING, Sentinel  # type: ignore",
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
""",
    )
