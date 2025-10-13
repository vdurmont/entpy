from ent_test_thing_pattern import EntTestThingPattern
from entpy import (
    Action,
    AllowAll,
    PrivacyRule,
    Field,
    Pattern,
    Schema,
    StringField,
)


class EntTestObject2Schema(Schema):
    def get_patterns(self) -> list[Pattern]:
        return [EntTestThingPattern()]

    def get_fields(self) -> list[Field]:
        return [StringField("some_field", 100)]

    def get_privacy_rules(self, action: Action) -> list[PrivacyRule]:
        return [AllowAll()]
