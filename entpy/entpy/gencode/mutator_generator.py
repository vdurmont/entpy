from entpy import Schema
from entpy.framework.fields.core import FieldWithDefault
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
        local_variables += f"        {field.name}: {field.get_python_type()}{or_not}\n"

    # TODO support UUID factory

    return GeneratedContent(
        code=f"""
class {base_name}MutatorCreationAction(EntMutatorCreationAction[{vc.name}, {base_name}, {base_name}Model]):
    ent_type = {base_name}
    model_type = {base_name}Model
    schema = {schema.__class__.__name__}()
    vc: {vc.name}

    if TYPE_CHECKING:
        id: UUID
{local_variables}
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
            f"        {field.name}: {field.get_python_type()}"
            + (" | None = None" if field.nullable else "")
            for field in mutable_fields
        ]
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
        imports=pattern_imports,
        code=f"""
class {base_name}MutatorUpdateAction({','.join(extends)}):
    ent_type = {base_name}
    model_type = {base_name}Model
    schema = {schema.__class__.__name__}()
    vc: {vc.name}
    ent: {base_name}

    if TYPE_CHECKING:
        id: UUID
{local_variables}
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
