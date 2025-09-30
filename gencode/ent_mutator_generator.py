from framework.ent_schema import EntSchema
from gencode.generated_content import GeneratedContent


def generate(
    schema: EntSchema,
    base_name: str,
    session_getter_fn_name: str,
) -> GeneratedContent:
    base = _generate_base(schema=schema, base_name=base_name)
    creation = _generate_creation(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
    )
    return GeneratedContent(
        imports=base.imports + creation.imports,
        code=base.code + "\n\n" + creation.code,
    )


def _generate_base(schema: EntSchema, base_name: str) -> GeneratedContent:
    # Separate nullable and non-nullable fields
    # We always process the mandatory fields first
    nullable_fields = [f for f in schema.get_fields() if f.nullable]
    non_nullable_fields = [f for f in schema.get_fields() if not f.nullable]

    # Build up the list of arguments the create function takes
    arguments_definition = ""
    for field in non_nullable_fields:
        arguments_definition += f", {field.name}: {field.get_python_type()}"
    for field in nullable_fields:
        arguments_definition += (
            f", {field.name}: {field.get_python_type()} | None = None"
        )

    # Build up the list of arguments the create function takes
    arguments_usage = "".join(
        [f", {field.name}" for field in non_nullable_fields]
        + [f", {field.name}" for field in nullable_fields]
    )

    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
        ],
        code=f"""
class {base_name}Mutator:
    @classmethod
    def create(
        cls, vc: ViewerContext{arguments_definition}
    ) -> {base_name}MutatorCreationAction:
        return {base_name}MutatorCreationAction(vc{arguments_usage})
""",
    )


def _generate_creation(
    schema: EntSchema, base_name: str, session_getter_fn_name: str
) -> GeneratedContent:
    # Separate nullable and non-nullable fields
    # We always process the mandatory fields first
    nullable_fields = [f for f in schema.get_fields() if f.nullable]
    nullable_fields.sort(key=lambda f: f.name)
    non_nullable_fields = [f for f in schema.get_fields() if not f.nullable]
    non_nullable_fields.sort(key=lambda f: f.name)

    # Build up the list of local variables we will store in the class
    local_variables = "\n".join(
        [
            f"    {field.name}: {field.get_python_type()}"
            for field in non_nullable_fields
        ]
        + [
            f"    {field.name}: {field.get_python_type()} = None"
            for field in nullable_fields
        ]
    )

    # Build up the list of arguments the create function takes
    arguments = ""
    for field in non_nullable_fields:
        arguments += f", {field.name}: {field.get_python_type()}"
    for field in nullable_fields:
        arguments += f", {field.name}: {field.get_python_type()} | None"

    # Build up the list of assignments in the constructor
    local_variables_assignments = "\n".join(
        [
            f"        self.{field.name} = {field.name}"
            for field in non_nullable_fields + nullable_fields
        ]
    )

    # Build up the list of variables to assign to the model
    model_assignments = "\n".join(
        [
            f"                {field.name}=self.{field.name},"
            for field in non_nullable_fields + nullable_fields
        ]
    )

    # TODO support UUID factory

    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
            "from uuid import UUID, uuid4",
        ],
        code=f"""
class {base_name}MutatorCreationAction:
    vc: ViewerContext
    id: UUID
{local_variables}

    def __init__(self, vc: ViewerContext{arguments}) -> None:
        self.vc = vc
        self.id = uuid4()
{local_variables_assignments}

    async def gen_savex(self) -> {base_name}:
        session = {session_getter_fn_name}()
        model = EntTestObjectModel(
            id=self.id,
{model_assignments}
        )
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await {base_name}._gen_from_model(self.vc, model)
""",
    )
