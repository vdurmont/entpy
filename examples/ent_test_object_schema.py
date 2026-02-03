import re
import uuid
from datetime import UTC, date, datetime, time, timedelta
from enum import Enum

from entpy import (
    Action,
    AllowAll,
    BoolField,
    DateField,
    DatetimeField,
    EdgeDelegate,
    EdgeField,
    EnumField,
    Field,
    FieldValidator,
    IntField,
    JsonField,
    Pattern,
    PrivacyRule,
    Schema,
    StringField,
    TextField,
    TimeField,
    IntervalField,
    UuidField,
)
from entpy.framework.composite_index import CompositeIndex

from ent_test_sub_object_schema import EntTestSubObjectSchema
from ent_test_thing_pattern import EntTestThingPattern


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
            StringField("firstname", 100).index().not_null().example("Vincent"),
            StringField("lastname", 100).default("Doe"),
            StringField("city", 100).example("Los Angeles").internal(),
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
            BoolField("is_it_true").example(False),
            UuidField("correlation_id"),
            UuidField("trace_id").dynamic_example(lambda: uuid.uuid4()),
            TimeField("start_time").example(time(9, 30, 0)),
            TimeField("end_time").dynamic_example(lambda: time(17, 30, 0)),
            DateField("dob").example(date(2000, 1, 1)),
            IntervalField("duration").example(timedelta(seconds=123.456)),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]

    def get_composite_indexes(self) -> list[CompositeIndex]:
        return [
            CompositeIndex(field_names=["trace_id", "status_code"], unique=True),
            CompositeIndex(field_names=["status", "sadness"]),
            CompositeIndex(
                field_names=["validated_field"],
                where="EntTestObjectModel.is_it_true.is_(True)",
            ),
        ]


class CustomValidator(FieldValidator[str | None]):
    def validate(self, value: str | None) -> bool:
        if not value:
            return True
        return bool(re.match(r"^[a-z0-9_-]+$", value))
