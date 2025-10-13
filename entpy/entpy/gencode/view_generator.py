from entpy.framework.pattern import Pattern
from entpy.framework.schema import Schema
from entpy.gencode.utils import to_snake_case


def generate(
    pattern_class: type[Pattern],
    children_schema_classes: list[type[Schema]],
) -> str:
    pattern = pattern_class()
    base_name = pattern_class.__name__.replace("Pattern", "")
    schemas = [s() for s in children_schema_classes]
    print(f"I got {len(schemas)} schemas")

    selects = ""
    imports = []
    for schema in schemas:
        schema_base_name = schema.__class__.__name__.replace("Schema", "")
        imports.append(
            f"from .{to_snake_case(schema_base_name)} import {schema_base_name}Model"
        )
        fields_code = ""
        for field in pattern.get_all_fields():
            fields_code += f"{schema_base_name}Model.{field.name},"
        selects += f"""    select(
        {schema_base_name}Model.id,
        {schema_base_name}Model.created_at,
        {schema_base_name}Model.updated_at,
        {fields_code}
        literal_column("'{schema_base_name}Model'").label("ent_type"),
    ),
"""

    imports_code = "\n".join(set(imports))

    return f"""
from sqlalchemy import literal_column, select, union_all, Table, Selectable
from sqlalchemy_utils import create_view
from .{to_snake_case(base_name)} import {base_name}Model
{imports_code}


view_query: Selectable = union_all(
{selects}
)


class {base_name}View({base_name}Model):
    __table__: Table = create_view(
        name="{to_snake_case(base_name)}_view",
        selectable=view_query,
        metadata={base_name}Model.metadata,
    )
"""
