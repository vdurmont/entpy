import uuid

from framework.ent_field import EntField, StringField
from framework.ent_schema import EntSchema


class EntTestObjectSchema(EntSchema):
    def get_fields(self) -> list[EntField]:
        return [
            StringField("username", 100)
            .not_null()
            .unique()
            .dynamic_example(lambda: str(uuid.uuid4())),
            StringField("firstname", 100).not_null().example("Vincent"),
            StringField("lastname", 100),
            StringField("city", 100).example("Los Angeles"),
        ]
