import re

from framework.ent_field import StringField
from framework.ent_schema import EntSchema
from gencode.generated_content import GeneratedContent


def generate(schema: EntSchema, base_name: str) -> GeneratedContent:
    fields = schema.get_fields()

    fields_code = ""
    for field in fields:
        common_column_attributes = ""
        if field.nullable:
            common_column_attributes += ", nullable=True"
        else:
            common_column_attributes += ", nullable=False"

        if isinstance(field, StringField):
            fields_code += f"    {field.name}: Mapped[str] = "
            fields_code += (
                f"mapped_column(String({field.length}){common_column_attributes})\n"
            )
        else:
            raise Exception(f"Unsupported field type: {type(field)}")

    return GeneratedContent(
        imports=[
            "from sqlalchemy import String",
            "from sqlalchemy.orm import Mapped, mapped_column",
        ],
        code=f"""
class {base_name}Model(EntModel):
    __tablename__ = "{_get_table_name(base_name)}"

{fields_code}
""",
    )


def _get_table_name(base_name: str) -> str:
    # Remove "Ent" prefix
    if base_name.startswith("Ent"):
        base_name = base_name[3:]

    # Convert CamelCase to snake_case
    # Insert underscore before uppercase letters (except first)
    base_name = re.sub(r"(?<!^)(?=[A-Z])", "_", base_name)

    # Convert to lowercase
    return base_name.lower()
