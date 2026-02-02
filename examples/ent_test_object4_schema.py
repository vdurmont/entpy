from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
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

    def get_privacy_config(
        self, action: Action
    ) -> PrivacyRule | EdgeDelegate | list[PrivacyRule | EdgeDelegate]:
        return [AllowAll()]
