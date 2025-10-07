import uuid

from ent_test_sub_object_schema import EntTestSubObjectSchema
from ent_test_thing_pattern import EntTestThingPattern
from entpy import EdgeField, Field, Pattern, Schema, StringField, TextField, EnumField
from enum import Enum


class Status(Enum):
    HAPPY = "HAPPY"
    SAD = "SAD"


class EntTestObjectSchema(Schema):
    def get_description(self):
        return "This is an object we use to test all the ent framework features!"

    def get_patterns(self) -> list[Pattern]:
        return [EntTestThingPattern()]

    def get_fields(self) -> list[Field]:
        return [
            StringField("username", 100)
            .not_null()
            .unique()
            .documentation("This is the username that you will use on the platform.")
            .dynamic_example(lambda: str(uuid.uuid4())),
            StringField("firstname", 100).not_null().example("Vincent"),
            StringField("lastname", 100),
            StringField("city", 100).example("Los Angeles"),
            EdgeField("self", EntTestObjectSchema),
            EdgeField("required_sub_object", EntTestSubObjectSchema).not_null(),
            EdgeField("optional_sub_object", EntTestSubObjectSchema),
            EdgeField("optional_sub_object_no_ex", EntTestSubObjectSchema).no_example(),
            TextField("context").example("This is some good context."),
            EnumField("status", Status).example(Status.HAPPY),
        ]
