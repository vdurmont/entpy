import re
import uuid
from datetime import datetime, UTC
from ent_test_sub_object_schema import EntTestSubObjectSchema
from ent_test_thing_pattern import EntTestThingPattern
from entpy import (
    Action,
    AllowAll,
    PrivacyRule,
    FieldValidator,
    EdgeField,
    JsonField,
    Field,
    IntField,
    Pattern,
    Schema,
    StringField,
    TextField,
    EnumField,
    DatetimeField,
)
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
            StringField("lastname", 100).default("Doe"),
            StringField("city", 100).example("Los Angeles"),
            EdgeField("self", EntTestObjectSchema),
            EdgeField("some_pattern", EntTestThingPattern),
            EdgeField("required_sub_object", EntTestSubObjectSchema).not_null(),
            EdgeField("optional_sub_object", EntTestSubObjectSchema),
            EdgeField("optional_sub_object_no_ex", EntTestSubObjectSchema).no_example(),
            TextField("context").example("This is some good context.").immutable(),
            EnumField("status", Status).example(Status.HAPPY),
            EnumField("sadness", Status).default(Status.SAD),
            DatetimeField("when_is_it_cool").dynamic_example(
                lambda: datetime.now(tz=UTC)
            ),
            IntField("status_code").example(404),
            JsonField("some_json", "list[str]").example(["hello", "world"]),
            StringField("validated_field", 100).validators([CustomValidator()]),
        ]

    def get_privacy_rules(self, action: Action) -> list[PrivacyRule]:
        return [AllowAll()]


class CustomValidator(FieldValidator[str | None]):
    def validate(self, value: str | None) -> bool:
        if not value:
            return True
        return bool(re.match(r"^[a-z0-9_-]+$", value))
