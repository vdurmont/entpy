from framework.schema import Schema
from gencode.generated_content import GeneratedContent


def generate(
    schema: Schema,
    base_name: str,
    session_getter_fn_name: str,
) -> GeneratedContent:
    base = _generate_base(schema=schema, base_name=base_name)
    creation = _generate_creation(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
    )
    update = _generate_update(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
    )
    deletion = _generate_deletion(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
    )
    return GeneratedContent(
        imports=base.imports + creation.imports + deletion.imports,
        code=base.code
        + "\n\n"
        + creation.code
        + "\n\n"
        + update.code
        + "\n\n"
        + deletion.code,
    )


def _generate_base(schema: Schema, base_name: str) -> GeneratedContent:
    # Build up the list of arguments the create function takes
    arguments_definition = ""
    for field in schema.get_sorted_fields():
        or_not = " | None = None" if field.nullable else ""
        arguments_definition += f", {field.name}: {field.get_python_type()}{or_not}"

    # Build up the list of arguments the create function takes
    arguments_usage = "".join(
        [f", {field.name}={field.name}" for field in schema.get_sorted_fields()]
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
        return {base_name}MutatorCreationAction(vc=vc{arguments_usage})

    @classmethod
    def update(
        cls, vc: ViewerContext, ent: {base_name}
    ) -> {base_name}MutatorUpdateAction:
        return {base_name}MutatorUpdateAction(vc=vc, ent=ent)

    @classmethod
    def delete(
        cls, vc: ViewerContext, ent: {base_name}
    ) -> {base_name}MutatorDeletionAction:
        return {base_name}MutatorDeletionAction(vc=vc, ent=ent)
""",
    )


def _generate_creation(
    schema: Schema,
    base_name: str,
    session_getter_fn_name: str,
) -> GeneratedContent:
    # Build up the list of local variables we will store in the class
    local_variables = ""
    for field in schema.get_sorted_fields():
        or_not = " | None = None" if field.nullable else ""
        local_variables += f"    {field.name}: {field.get_python_type()}{or_not}\n"

    # Build up the list of arguments the __init__ function takes
    constructor_arguments = ""
    for field in schema.get_sorted_fields():
        or_not = " | None" if field.nullable else ""
        constructor_arguments += f", {field.name}: {field.get_python_type()}{or_not}"

    # Build up the list of assignments in the constructor
    constructor_assignments = "\n".join(
        [
            f"        self.{field.name} = {field.name}"
            for field in schema.get_sorted_fields()
        ]
    )

    # Build up the list of variables to assign to the model
    model_assignments = "\n".join(
        [
            f"                {field.name}=self.{field.name},"
            for field in schema.get_sorted_fields()
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

    def __init__(self, vc: ViewerContext{constructor_arguments}) -> None:
        self.vc = vc
        self.id = uuid4()
{constructor_assignments}

    async def gen_savex(self) -> {base_name}:
        session = {session_getter_fn_name}()
        model = {base_name}Model(
            id=self.id,
{model_assignments}
        )
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await {base_name}._genx_from_model(self.vc, model)
""",
    )


def _generate_update(
    schema: Schema, base_name: str, session_getter_fn_name: str
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
            f"    {field.name}: {field.get_python_type()} | None = None"
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
            f"        self.{field.name} = ent.{field.name}"
            for field in non_nullable_fields + nullable_fields
        ]
    )

    # Build up the list of variables to assign to the model
    model_assignments = "\n".join(
        [
            f"        model.{field.name}=self.{field.name}"
            for field in non_nullable_fields + nullable_fields
        ]
    )

    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
            "from uuid import UUID, uuid4",
        ],
        code=f"""
class {base_name}MutatorUpdateAction:
    vc: ViewerContext
    ent: {base_name}
    id: UUID
{local_variables}

    def __init__(self, vc: ViewerContext, ent: {base_name}) -> None:
        self.vc = vc
        self.ent = ent
{local_variables_assignments}

    async def gen_savex(self) -> {base_name}:
        session = {session_getter_fn_name}()
        model = self.ent.model
{model_assignments}
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await {base_name}._genx_from_model(self.vc, model)
""",
    )


def _generate_deletion(
    schema: Schema, base_name: str, session_getter_fn_name: str
) -> GeneratedContent:
    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
        ],
        code=f"""
class {base_name}MutatorDeletionAction:
    vc: ViewerContext
    ent: {base_name}

    def __init__(self, vc: ViewerContext, ent: {base_name}) -> None:
        self.vc = vc
        self.ent = ent

    async def gen_save(self) -> None:
        session = {session_getter_fn_name}()
        model = self.ent.model
        # TODO privacy checks
        await session.delete(model)
        await session.flush()
""",
    )
