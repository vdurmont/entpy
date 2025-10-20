from entpy import Schema
from entpy.framework.fields.core import Field
from entpy.gencode.generated_content import GeneratedContent


def generate(
    schema: Schema, base_name: str, session_getter_fn_name: str, vc_name: str
) -> GeneratedContent:
    base = _generate_base(schema=schema, base_name=base_name, vc_name=vc_name)
    creation = _generate_creation(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
        vc_name=vc_name,
    )
    update = _generate_update(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
        vc_name=vc_name,
    )
    deletion = _generate_deletion(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
        vc_name=vc_name,
    )
    return GeneratedContent(
        imports=base.imports + creation.imports + update.imports + deletion.imports,
        code=base.code
        + "\n\n"
        + creation.code
        + "\n\n"
        + update.code
        + "\n\n"
        + deletion.code,
    )


def _generate_base(schema: Schema, base_name: str, vc_name: str) -> GeneratedContent:
    # Build up the list of arguments the create function takes
    arguments_definition = ""
    for field in schema.get_all_fields():
        or_not = " | None = None" if field.nullable else ""
        arguments_definition += f", {field.name}: {field.get_python_type()}{or_not}"

    # Build up the list of arguments the create function takes
    arguments_usage = "".join(
        [f", {field.name}={field.name}" for field in schema.get_all_fields()]
    )

    # If the schema is not immutable, we generate the update
    update_function = (
        ""
        if schema.is_immutable()
        else f"""
    @classmethod
    def update(
        cls, vc: {vc_name}, ent: {base_name}
    ) -> {base_name}MutatorUpdateAction:
        return {base_name}MutatorUpdateAction(vc=vc, ent=ent)
"""
    )

    return GeneratedContent(
        code=f"""
class {base_name}Mutator:
    @classmethod
    def create(
        cls, vc: {vc_name}{arguments_definition}, id: UUID | None = None, created_at: datetime | None = None
    ) -> {base_name}MutatorCreationAction:
        return {base_name}MutatorCreationAction(vc=vc, id=id, created_at=created_at{arguments_usage})
{update_function}
    @classmethod
    def delete(
        cls, vc: {vc_name}, ent: {base_name}
    ) -> {base_name}MutatorDeletionAction:
        return {base_name}MutatorDeletionAction(vc=vc, ent=ent)
""",  # noqa: E501
    )


def _generate_creation(
    schema: Schema, base_name: str, session_getter_fn_name: str, vc_name: str
) -> GeneratedContent:
    fields = schema.get_all_fields()

    # Build up the list of local variables we will store in the class
    local_variables = ""
    for field in fields:
        or_not = " | None = None" if field.nullable else ""
        local_variables += f"    {field.name}: {field.get_python_type()}{or_not}\n"

    # Build up the list of arguments the __init__ function takes
    constructor_arguments = ""
    for field in fields:
        or_not = " | None" if field.nullable else ""
        constructor_arguments += f", {field.name}: {field.get_python_type()}{or_not}"

    # Build up the list of assignments in the constructor
    constructor_assignments = "\n".join(
        [f"        self.{field.name} = {field.name}" for field in fields]
    )

    validations = _generate_validations(base_name=base_name, fields=fields)

    # Build up the list of variables to assign to the model
    model_assignments = "\n".join(
        [f"                {field.name}=self.{field.name}," for field in fields]
    )

    # TODO support UUID factory

    return GeneratedContent(
        imports=validations.imports,
        code=f"""
class {base_name}MutatorCreationAction:
    vc: {vc_name}
    id: UUID
{local_variables}

    def __init__(self, vc: {vc_name}, id: UUID | None, created_at: datetime | None{constructor_arguments}) -> None:
        self.vc = vc
        self.created_at = created_at if created_at else datetime.now(tz=UTC)
        self.id = id if id else generate_uuid({base_name}, self.created_at)
{constructor_assignments}

    async def gen_savex(self) -> {base_name}:
        session = {session_getter_fn_name}()
{validations.code}
        model = {base_name}Model(
            id=self.id,
            created_at=self.created_at,
{model_assignments}
        )
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await {base_name}._genx_from_model(self.vc, model)
""",  # noqa: E501
    )


def _generate_update(
    schema: Schema, base_name: str, session_getter_fn_name: str, vc_name: str
) -> GeneratedContent:
    if schema.is_immutable():
        return GeneratedContent("")

    fields = schema.get_all_fields()
    mutable_fields = list(filter(lambda f: not f.is_immutable, fields))

    # Build up the list of local variables we will store in the class
    local_variables = "\n".join(
        [
            f"    {field.name}: {field.get_python_type()}"
            + (" | None = None" if field.nullable else "")
            for field in mutable_fields
        ]
    )

    # Build up the list of assignments in the constructor
    local_variables_assignments = "\n".join(
        [f"        self.{field.name} = ent.{field.name}" for field in mutable_fields]
    )

    validations = _generate_validations(base_name=base_name, fields=mutable_fields)

    # Build up the list of variables to assign to the model
    model_assignments = "\n".join(
        [f"        model.{field.name}=self.{field.name}" for field in mutable_fields]
    )

    return GeneratedContent(
        imports=validations.imports,
        code=f"""
class {base_name}MutatorUpdateAction:
    vc: {vc_name}
    ent: {base_name}
    id: UUID
{local_variables}

    def __init__(self, vc: {vc_name}, ent: {base_name}) -> None:
        self.vc = vc
        self.ent = ent
{local_variables_assignments}

    async def gen_savex(self) -> {base_name}:
        session = {session_getter_fn_name}()
{validations.code}
        model = self.ent.model
{model_assignments}
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await {base_name}._genx_from_model(self.vc, model)
""",
    )


def _generate_deletion(
    schema: Schema, base_name: str, session_getter_fn_name: str, vc_name: str
) -> GeneratedContent:
    return GeneratedContent(
        code=f"""
class {base_name}MutatorDeletionAction:
    vc: {vc_name}
    ent: {base_name}

    def __init__(self, vc: {vc_name}, ent: {base_name}) -> None:
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


def _generate_validations(base_name: str, fields: list[Field]) -> GeneratedContent:
    validations = ""
    for field in fields:
        if field._validators:
            validations += f"""
        {field.name}_validators = _get_field("{field.name}")._validators
        for validator in {field.name}_validators:
            if not validator.validate(self.{field.name}):
                raise ValidationError("Invalid value for {base_name}.{field.name}")
"""
    return GeneratedContent(
        imports=["from entpy import ValidationError"] if validations else [],
        code=validations,
    )
