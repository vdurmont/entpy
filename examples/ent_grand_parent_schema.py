from entpy import Field, Schema, StringField, Action, AllowAll, PrivacyRule


class EntGrandParentSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("Anne"),
        ]

    def get_privacy_rules(self, action: Action) -> list[PrivacyRule]:
        return [AllowAll()]
