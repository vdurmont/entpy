from entpy import (
    BoolField,
    CompositeIndex,
    DateField,
    DatetimeField,
    EdgeField,
    EnumField,
    IntervalField,
    IntField,
    JsonField,
    Pattern,
    Schema,
    StringField,
    TextField,
    TimeField,
    UuidField,
)
from entpy.framework.descriptor import Descriptor
from entpy.framework.fields.bytes_field import BytesField
from entpy.framework.fields.core import FieldWithDefault
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


def generate(descriptor: Descriptor, base_name: str) -> GeneratedContent:
    # Only use the fields for this specific descriptor. The patterns fields will
    # be handled by inheritance.
    fields = descriptor.get_sorted_fields()

    fields_code = ""
    types_imports = []
    type_checking_imports = []
    for field in fields:
        common_column_attributes = ", nullable=" + (
            "True" if field.nullable else "False"
        )
        if isinstance(field, FieldWithDefault):
            default = field.generate_sql_default()
            if default:
                common_column_attributes += f", server_default={default}"

        mapped_type = (
            field.get_python_type() + " | None"
            if field.nullable
            else field.get_python_type()
        )

        if isinstance(field, BoolField):
            types_imports.append("from sqlalchemy import Boolean")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Boolean(){common_column_attributes})\n"
        elif isinstance(field, BytesField):
            types_imports.append("from sqlalchemy import LargeBinary")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(LargeBinary(){common_column_attributes})\n"
        elif isinstance(field, DateField):
            types_imports.append("from sqlalchemy import Date")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Date(){common_column_attributes})\n"
        elif isinstance(field, DatetimeField):
            types_imports.append("from entpy.types import DateTime")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(DateTime(){common_column_attributes})\n"
        elif isinstance(field, EnumField):
            type_name = field.enum_class.__name__
            types_imports.append("from sqlalchemy import Enum as DBEnum")
            types_imports.append(_generate_enum_import(field))
            mapped_type = type_name + " | None" if field.nullable else type_name
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(DBEnum({type_name}, native_enum=True)"
            fields_code += f"{common_column_attributes})\n"
        elif isinstance(field, IntField):
            types_imports.append("from sqlalchemy import Integer")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Integer(){common_column_attributes})\n"
        elif isinstance(field, JsonField):
            types_imports.append("from sqlalchemy import JSON")
            types_imports.append("from sqlalchemy.dialects.postgresql import JSONB")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f'mapped_column(JSON().with_variant(JSONB(), "postgresql"){common_column_attributes})\n'
        elif isinstance(field, StringField):
            types_imports.append("from sqlalchemy import String")
            attributes = ", collation='nocase'" if not field.case_sensitive else ""
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(String({field.length}{attributes}){common_column_attributes})\n"
        elif isinstance(field, TextField):
            types_imports.append("from sqlalchemy import Text")
            attributes = ", collation='nocase'" if not field.case_sensitive else ""
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += (
                f"mapped_column(Text({attributes}){common_column_attributes})\n"
            )
        elif isinstance(field, TimeField):
            types_imports.append("from sqlalchemy import Time")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Time(){common_column_attributes})\n"
        elif isinstance(field, IntervalField):
            types_imports.append("from sqlalchemy import Interval")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Interval(){common_column_attributes})\n"
        elif isinstance(field, UuidField):
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Uuid(){common_column_attributes})\n"
        elif isinstance(field, EdgeField):
            types_imports.append("from sqlalchemy import ForeignKey")
            edge_base_name = field.edge_class.__name__.removesuffix(
                "Schema"
            ).removesuffix("Pattern")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += "mapped_column(Uuid()"
            if not field.edge_class.__name__.endswith("Pattern"):
                # Cannot do FKs for Patterns
                fields_code += f', ForeignKey("{field.edge_class.get_qualified_table_name()}.id", deferrable=True, initially="DEFERRED")'
            fields_code += f"{common_column_attributes})\n"
        else:
            raise Exception(f"Unsupported field type: {type(field)}")

    # Add imports for EnumFields only
    all_fields = descriptor.get_all_fields()
    for field in all_fields:
        if isinstance(field, EnumField):
            types_imports.append(_generate_enum_import(field))

    if isinstance(descriptor, Schema):
        for field in descriptor.get_all_fields():
            if isinstance(field, EdgeField) and issubclass(field.edge_class, Schema):
                types_imports.append("from sqlalchemy.orm import relationship")
                edge_base_name = field.edge_class.__name__.removesuffix("Schema")
                module = "." + to_snake_case(edge_base_name)
                if base_name != edge_base_name:
                    type_checking_imports.append(
                        f"from {module} import {edge_base_name}Model"
                    )

                fields_code += (
                    f'    {field.original_name}: Mapped["{edge_base_name}Model"] = '
                )
                fields_code += f'relationship("{edge_base_name}Model", primaryjoin="{base_name}Model.{field.name} == {edge_base_name}Model.id")\n'

    indexes = (
        _generate_indexes(schema=descriptor, base_name=base_name)
        if isinstance(descriptor, Schema)
        else GeneratedContent("")
    )

    triggers = (
        _generate_triggers(descriptor=descriptor, base_name=base_name)
        if isinstance(descriptor, Schema)
        else GeneratedContent("")
    )

    metadata = (
        "__abstract__ = True"
        if isinstance(descriptor, Pattern)
        else f'__tablename__ = "{descriptor.get_table_name()}"'
    )
    if descriptor.get_table_schema():
        metadata += f'\n    __table_args__ = {"{"}"schema": "{descriptor.get_table_schema()}"{"}"}'

    extends = _generate_extends(descriptor=descriptor)

    return GeneratedContent(
        imports=[
            "from sqlalchemy.orm import Mapped, mapped_column",
            "from entpy.framework.types import Uuid",
            "from .ent_model import EntModel",
        ]
        + types_imports
        + indexes.imports
        + extends.imports
        + triggers.imports,
        type_checking_imports=type_checking_imports,
        code=f"""
class {base_name}Model({extends.code}):
    {metadata}

{fields_code}

{indexes.code}

{triggers.code}
""",
    )


def _generate_enum_import(field: EnumField) -> str:
    module = field.enum_class.__module__
    type_name = field.enum_class.__name__
    return f"from {module} import {type_name}"


def _generate_indexes(schema: Schema, base_name: str) -> GeneratedContent:
    indexes = schema.get_all_composite_indexes()
    for field in schema.get_all_fields():
        if field.is_indexed or field.is_unique:
            indexes.append(
                CompositeIndex(
                    field_names=[field.name],
                    unique=field.is_unique,
                )
            )

    return GeneratedContent(
        imports=["from sqlalchemy import Index, text"] if indexes else [],
        code="\n".join(
            [_generate_index(index=index, base_name=base_name) for index in indexes]
        ),
    )


def _generate_index(index: CompositeIndex, base_name: str) -> str:
    return f"""Index(
    None,
{"\n".join([f"    {base_name}Model.{field_name}," for field_name in index.field_names])}
{"    unique = True," if index.unique else ""}
{f"    postgresql_where = {index.where}," if index.where else ""}
{f"    sqlite_where = {index.where}," if index.where else ""}
)"""


def _generate_extends(descriptor: Descriptor) -> GeneratedContent:
    patterns = descriptor.get_patterns()
    code = ", ".join(
        [p.__class__.__name__.removesuffix("Pattern") + "Model" for p in patterns]
    )

    def get_import(pattern: Pattern) -> str:
        base_name = pattern.__class__.__name__.removesuffix("Pattern")
        return f"from .{to_snake_case(base_name)} import {base_name}Model"

    imports = [get_import(p) for p in patterns]
    return (
        GeneratedContent(code=code, imports=imports)
        if code
        else GeneratedContent(code="EntModel")
    )


def gen_trigger_events(
    base_name: str, pattern: str, table: str, columns: list[str]
) -> str:
    column_list = ", ".join([f'"{column}"' for column in columns])
    return f"""
event.listen(
    {base_name}Model.__table__,
    "after_create",
    CreatePatternUniqueFunctionPostgres("{pattern}", "{table}", [{column_list}]).execute_if(dialect="postgresql"),
)
event.listen(
    {base_name}Model.__table__,
    "after_create",
    CreatePatternUniqueTriggerPostgres("{pattern}", "{table}", [{column_list}]).execute_if(dialect="postgresql"),
)
event.listen(
    {base_name}Model.__table__,
    "after_create",
    CreatePatternUniqueTriggerSqlite("insert", "{pattern}", "{table}", [{column_list}]).execute_if(dialect="sqlite"),
)
event.listen(
    {base_name}Model.__table__,
    "after_create",
    CreatePatternUniqueTriggerSqlite("update", "{pattern}", "{table}", [{column_list}]).execute_if(dialect="sqlite"),
)
"""


def _generate_triggers(descriptor: Descriptor, base_name: str) -> GeneratedContent:
    code = ""
    for pattern in descriptor.get_patterns():
        for field in pattern.get_fields():
            if field.is_unique_pattern:
                code += gen_trigger_events(
                    base_name,
                    pattern.get_table_name(),
                    descriptor.get_table_name(),
                    [field.name],
                )
        for index in pattern.get_composite_indexes():
            if index.unique:
                code += gen_trigger_events(
                    base_name,
                    pattern.get_table_name(),
                    descriptor.get_table_name(),
                    index.field_names,
                )

    if code:
        return GeneratedContent(
            code=code,
            imports=[
                "from sqlalchemy import event, DDL",
                "from entpy.framework.triggers import CreatePatternUniqueFunctionPostgres, CreatePatternUniqueTriggerPostgres, CreatePatternUniqueTriggerSqlite",
            ],
        )
    else:
        return GeneratedContent("")
