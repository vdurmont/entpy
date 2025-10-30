from entpy import (
    Action,
    AllowAll,
    PrivacyRule,
    EdgeField,
    Field,
    Schema,
)

from ent_test_object3_schema import EntTestObject3Schema


class EntTestObject4Schema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("other", EntTestObject3Schema),
        ]

    def get_privacy_rules(self, action: Action) -> list[PrivacyRule]:
        return [AllowAll()]
