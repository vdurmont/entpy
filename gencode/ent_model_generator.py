from framework.ent_field import StringField
from framework.ent_schema import EntSchema
from gencode.generated_content import GeneratedContent


class EntModelGenerator:
    base_name: str

    def __init__(self, schema: EntSchema, base_name: str):
        self.schema = schema
        self.base_name = base_name

    def generate(self) -> GeneratedContent:
        fields = self.schema.get_fields()

        fields_code = ""
        for field in fields:
            print(f"Field: {field.name}")
            if isinstance(field, StringField):
                fields_code += f"   {field.name}: Mapped[str] = "
                fields_code += f"mapped_column(String({field.length}))\n"
            else:
                raise Exception(f"Unsupported field type: {type(field)}")

        return GeneratedContent(
            imports=[
                "from examples.database import Base",  # TODO nope.
                "from sqlalchemy import String",
                "from sqlalchemy.orm import Mapped, mapped_column",
            ],
            code=f"""
class {self.base_name}Model(Base):
    {fields_code}
""",
        )
