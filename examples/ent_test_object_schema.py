import uuid

from examples.ent_test_sub_object_schema import EntTestSubObjectSchema
from framework.ent_field import EdgeField, EntField, StringField
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
            EdgeField("required_sub_object", EntTestSubObjectSchema).not_null(),
            EdgeField("optional_sub_object", EntTestSubObjectSchema),
            EdgeField("optional_sub_object_no_ex", EntTestSubObjectSchema).no_example(),
        ]
