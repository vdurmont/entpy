from entpy import JsonField, Schema
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
    # Collect Pydantic imports
    imports = []

    # Build up the list of arguments the create function takes
    arguments_definition = ""
    for field in schema.get_all_fields():
        # For Pydantic JsonFields, accept both Pydantic instances and dicts
        if isinstance(field, JsonField) and field.is_pydantic_field():
            pydantic_import = field.get_pydantic_model_import()
            if pydantic_import:
                imports.append(pydantic_import)
            pydantic_type = field.get_entity_property_type()
            field_type = f"{pydantic_type} | dict[str, Any]"
        else:
            field_type = field.get_python_type()

        or_not = ""
        if field.nullable:
            or_not = " | None = None"
        elif isinstance(field, FieldWithDefault):
            default = field.generate_default()
            if default:
                or_not = f" = {default}"
        arguments_definition += f", {field.name}: {field_type}{or_not}"

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
        imports=imports,
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

    # Collect Pydantic imports
    imports = []
    pydantic_fields = []

    # Build up the list of local variables we will store in the class
    local_variables = ""
    for field in fields:
        # For Pydantic JsonFields, accept both Pydantic instances and dicts
        if isinstance(field, JsonField) and field.is_pydantic_field():
            pydantic_import = field.get_pydantic_model_import()
            if pydantic_import:
                imports.append(pydantic_import)
            pydantic_type = field.get_entity_property_type()
            field_type = f"{pydantic_type} | dict[str, Any]"
            pydantic_fields.append(field.name)
        else:
            field_type = field.get_python_type()

        or_not = " | None = None" if field.nullable else ""
        local_variables += f"        {field.name}: {field_type}{or_not}\n"

    # Generate __init__ override and __setattr__ if there are Pydantic fields
    init_override = ""
    setattr_override = ""
    if pydantic_fields:
        imports.append("from typing import Any")
        imports.append("from datetime import datetime, UTC")
        imports.append("from uuid import UUID")

        # Generate __init__ to handle Pydantic serialization before model creation
        init_override = f"""
    def __init__(
        self,
        vc: {vc.name},
        id: UUID | None,
        created_at: datetime | None,
        updated_at: datetime | None,
        **kwargs: Any,
    ) -> None:
        # Process Pydantic fields before passing to model
"""
        for field_name in pydantic_fields:
            field = next(f for f in fields if f.name == field_name)
            model_class = field.get_entity_property_type()  # type: ignore
            init_override += f"""        if "{field_name}" in kwargs and kwargs["{field_name}"] is not None:
            value = kwargs["{field_name}"]
            if isinstance(value, {model_class}):
                kwargs["{field_name}"] = value.model_dump(mode='json')
            elif isinstance(value, dict):
                kwargs["{field_name}"] = {model_class}.model_validate(value).model_dump(mode='json')
"""
        init_override += """        super().__init__(vc=vc, id=id, created_at=created_at, updated_at=updated_at, **kwargs)

"""

        setattr_override = """    if not TYPE_CHECKING:
        def __setattr__(self, name: str, value: Any) -> None:
            if hasattr(self, "model") and name in self.model.__table__.columns:
                # Handle Pydantic JsonFields
"""
        for field_name in pydantic_fields:
            field = next(f for f in fields if f.name == field_name)
            model_class = field.get_entity_property_type()  # type: ignore
            setattr_override += f"""                if name == "{field_name}" and value is not None:
                    # Accept both Pydantic instances and dicts
                    if isinstance(value, {model_class}):
                        value = value.model_dump(mode='json')
                    elif isinstance(value, dict):
                        # Validate dict by parsing it
                        value = {model_class}.model_validate(value).model_dump(mode='json')
"""
        setattr_override += """                setattr(self.model, name, value)
            else:
                super().__setattr__(name, value)
"""

    # TODO support UUID factory

    return GeneratedContent(
        imports=imports,
        code=f"""
class {base_name}MutatorCreationAction(EntMutatorCreationAction[{vc.name}, {base_name}, {base_name}Model]):
    ent_type = {base_name}
    model_type = {base_name}Model
    schema = {schema.__class__.__name__}()
    vc: {vc.name}

    if TYPE_CHECKING:
        id: UUID
{local_variables}
{init_override}
{setattr_override}
""",  # noqa: E501
    )


def _generate_update(
    schema: Schema, base_name: str, vc: ImportedObject
) -> GeneratedContent:
    if schema.is_immutable():
        return GeneratedContent("")

    fields = schema.get_all_fields()
    mutable_fields = list(filter(lambda f: not f.is_immutable, fields))

    # Collect Pydantic imports
    imports: list[str] = []
    pydantic_fields = []

    # Build up the list of local variables we will store in the class
    local_variables = []
    for field in mutable_fields:
        # For Pydantic JsonFields, accept both Pydantic instances and dicts
        if isinstance(field, JsonField) and field.is_pydantic_field():
            pydantic_import = field.get_pydantic_model_import()
            if pydantic_import:
                imports.append(pydantic_import)
            pydantic_type = field.get_entity_property_type()
            field_type = f"{pydantic_type} | dict[str, Any]"
            pydantic_fields.append(field.name)
        else:
            field_type = field.get_python_type()

        local_variables.append(
            f"        {field.name}: {field_type}"
            + (" | None = None" if field.nullable else "")
        )

    local_variables_str = "\n".join(local_variables)

    # Generate __setattr__ override if there are Pydantic fields
    setattr_override = ""
    if pydantic_fields:
        imports.append("from typing import Any")
        setattr_override = """
    if not TYPE_CHECKING:
        def __setattr__(self, name: str, value: Any) -> None:
            if hasattr(self, "model") and name in self.model.__table__.columns:
                # Handle Pydantic JsonFields
"""
        for field_name in pydantic_fields:
            field = next(f for f in mutable_fields if f.name == field_name)
            model_class = field.get_entity_property_type()  # type: ignore
            setattr_override += f"""                if name == "{field_name}" and value is not None:
                    # Accept both Pydantic instances and dicts
                    if isinstance(value, {model_class}):
                        value = value.model_dump(mode='json')
                    elif isinstance(value, dict):
                        # Validate dict by parsing it
                        value = {model_class}.model_validate(value).model_dump(mode='json')
"""
        setattr_override += """                self._updates[name] = value
            else:
                super().__setattr__(name, value)
"""

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
        imports=pattern_imports + imports,
        code=f"""
class {base_name}MutatorUpdateAction({','.join(extends)}):
    ent_type = {base_name}
    model_type = {base_name}Model
    schema = {schema.__class__.__name__}()
    vc: {vc.name}
    ent: {base_name}

    if TYPE_CHECKING:
        id: UUID
{local_variables_str}
{setattr_override}
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
