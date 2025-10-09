from entpy import Field, Schema, StringField, Action, AllowAll, PrivacyRule


class EntTestSubObjectSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("email", 100).not_null().example("vdurmont@gmail.com"),
        ]

    def get_privacy_rules(self, action: Action) -> list[PrivacyRule]:
        return [AllowAll()]
