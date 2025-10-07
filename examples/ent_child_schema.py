from entpy import Field, Schema, StringField, EdgeField
from ent_parent_schema import EntParentSchema


class EntChildSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("parent", EntParentSchema).not_null(),
            StringField("name", 100).not_null().example("Benjamin"),
        ]
