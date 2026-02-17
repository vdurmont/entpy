from entpy import Schema
from entpy.framework.fields.core import Field, FieldWithDefault
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import ImportedObject
from entpy.gencode.utils import to_snake_case as _to_snake_case


def generate(schema: Schema, base_name: str, vc: ImportedObject) -> GeneratedContent:
    base = _generate_base(schema=schema, base_name=base_name, vc=vc)
    creation = _generate_creation(schema=schema, base_name=base_name, vc=vc)
    update = _generate_update(schema=schema, base_name=base_name, vc=vc)
    deletion = _generate_deletion(schema=schema, base_name=base_name, vc=vc)
    return GeneratedContent(
        imports=[
            "from entpy import PrivacyError",
            "from entpy.framework.mutators import EntMutatorCreationAction, EntMutatorUpdateAction, EntMutatorDeletionAction",
        ]
        + base.imports
        + creation.imports
        + update.imports
        + deletion.imports,
        code=base.code
        + "\n\n"
        + creation.code
        + "\n\n"
        + update.code
        + "\n\n"
        + deletion.code,
    )


def _generate_base(
    schema: Schema, base_name: str, vc: ImportedObject
) -> GeneratedContent:
    # Build up the list of arguments the create function takes
    arguments_definition = ""
    for field in schema.get_all_fields():
        or_not = ""
        if field.nullable:
            or_not = " | None = None"
        elif isinstance(field, FieldWithDefault):
            default = field.generate_default()
            if default:
                or_not = f" = {default}"
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
        cls, vc: {vc.name}, ent: {base_name}
    ) -> {base_name}MutatorUpdateAction:
        return {base_name}MutatorUpdateAction(vc=vc, ent=ent)
"""
    )

    return GeneratedContent(
        code=f"""
class {base_name}Mutator:
    @classmethod
    def create(
        cls, vc: {vc.name}{arguments_definition}, id: UUID | None = None, created_at: datetime | None = None, updated_at: datetime | None = None
    ) -> {base_name}MutatorCreationAction:
        return {base_name}MutatorCreationAction(vc=vc, id=id, created_at=created_at, updated_at=updated_at{arguments_usage})
{update_function}
    @classmethod
    def hard_delete(
        cls, vc: {vc.name}, ent: {base_name}
    ) -> {base_name}MutatorDeletionAction:
        return {base_name}MutatorDeletionAction(vc=vc, ent=ent, is_soft_delete=False)

    @classmethod
    def soft_delete(
        cls, vc: {vc.name}, ent: {base_name}
    ) -> {base_name}MutatorDeletionAction:
        return {base_name}MutatorDeletionAction(vc=vc, ent=ent, is_soft_delete=True)
""",  # noqa: E501
    )


def _generate_creation(
    schema: Schema, base_name: str, vc: ImportedObject
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
class {base_name}MutatorCreationAction(EntMutatorCreationAction[{vc.name}, {base_name}, {base_name}Model]):
    ent_type = {base_name}
    vc: {vc.name}
    id: UUID
{local_variables}

    def __init__(self, vc: {vc.name}, id: UUID | None, created_at: datetime | None, updated_at: datetime | None{constructor_arguments}) -> None:
        self.vc = vc
        self.created_at = created_at if created_at else datetime.now(tz=UTC)
        self.updated_at = updated_at if updated_at else self.created_at
        self.id = id if id else generate_uuid({base_name}, self.created_at)
{constructor_assignments}

    def _validate(self) -> None:
{validations.code or "        pass"}

    def _create_model(self) -> {base_name}Model:
        return {base_name}Model(
            id=self.id,
            updated_at=self.updated_at,
            created_at=self.created_at,
{model_assignments}
        )
""",  # noqa: E501
    )


def _generate_update(
    schema: Schema, base_name: str, vc: ImportedObject
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

    # Check if the schema has patterns to determine inheritance
    extends = [f"EntMutatorUpdateAction[{vc.name}, {base_name}, {base_name}Model]"]
    pattern_imports: list[str] = []
    patterns = schema.get_patterns()
    if patterns:
        # Use all patterns for multiple inheritance
        pattern_imports = []
        for pattern in patterns:
            pattern_base_name = pattern.__class__.__name__.removesuffix("Pattern")
            extends.append(f"I{pattern_base_name}MutatorUpdateAction")
            pattern_imports.append(
                f"from .{_to_snake_case(pattern_base_name)} "
                + f"import I{pattern_base_name}MutatorUpdateAction"
            )

    return GeneratedContent(
        imports=validations.imports + pattern_imports,
        code=f"""
class {base_name}MutatorUpdateAction({','.join(extends)}):
    ent_type = {base_name}
    vc: {vc.name}
    ent: {base_name}
    id: UUID
{local_variables}

    def __init__(self, vc: {vc.name}, ent: {base_name}) -> None:
        self.vc = vc
        self.ent = ent
{local_variables_assignments}

    def _validate(self) -> None:
{validations.code or "        pass"}

    def _update_model(self, model: {base_name}Model) -> {base_name}Model:
{model_assignments}
        return model
""",
    )


def _generate_deletion(
    schema: Schema, base_name: str, vc: ImportedObject
) -> GeneratedContent:
    # Check if the schema has patterns to determine inheritance
    extends = [f"EntMutatorDeletionAction[{vc.name}, {base_name}, {base_name}Model]"]
    pattern_imports: list[str] = []
    patterns = schema.get_patterns()
    if patterns:
        # Use all patterns for multiple inheritance
        pattern_imports = []
        for pattern in patterns:
            pattern_base_name = pattern.__class__.__name__.removesuffix("Pattern")
            extends.append(f"I{pattern_base_name}MutatorDeletionAction")
            pattern_imports.append(
                f"from .{_to_snake_case(pattern_base_name)} "
                + f"import I{pattern_base_name}MutatorDeletionAction"
            )

    return GeneratedContent(
        imports=pattern_imports,
        code=f"""
class {base_name}MutatorDeletionAction(  {"# type: ignore[misc]" if patterns else ""}
    {','.join(extends)}
):
    ent_type = {base_name}
""",
    )


def _generate_validations(base_name: str, fields: list[Field]) -> GeneratedContent:
    validations = ""
    for field in fields:
        if field._validators:
            validations += f"""
        {field.name}_validators = _get_field("{field.name}")._validators  # noqa: SLF001
        for validator in {field.name}_validators:
            if not validator.validate(self.{field.name}):
                raise ValidationError("Invalid value for {base_name}.{field.name}")
"""
    return GeneratedContent(
        imports=["from entpy import ValidationError"] if validations else [],
        code=validations,
    )
