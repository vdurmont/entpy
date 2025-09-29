from framework.ent_field import EntField, StringField
from framework.ent_schema import EntSchema


class EntTestObjectSchema(EntSchema):
    def get_fields(self) -> list[EntField]:
        return [
            StringField("firstname", 100).not_null(),
            StringField("lastname", 100),
        ]
