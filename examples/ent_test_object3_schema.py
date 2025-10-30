from entpy import (
    Action,
    AllowAll,
    PrivacyRule,
    EdgeField,
    Field,
    Schema,
)


class EntTestObject3Schema(Schema):
    def get_fields(self) -> list[Field]:
        from ent_test_object4_schema import EntTestObject4Schema

        return [
            EdgeField("other", EntTestObject4Schema),
        ]

    def get_privacy_rules(self, action: Action) -> list[PrivacyRule]:
        return [AllowAll()]
