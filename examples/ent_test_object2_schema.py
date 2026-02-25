from ent_test_thing_pattern import EntTestThingPattern
from ent_test_pattern_pattern import EntTestPatternPattern
from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
    PrivacyRule,
    Field,
    Pattern,
    Schema,
    StringField,
)


class EntTestObject2Schema(Schema):
    def get_patterns(self) -> list[Pattern]:
        return [EntTestThingPattern(), EntTestPatternPattern()]

    def get_fields(self) -> list[Field]:
        return [StringField("some_field", 100)]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]

    def get_event_fields(self) -> list[str]:
        return ["id", "some_field"]
