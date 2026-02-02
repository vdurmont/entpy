from entpy import (
    Field,
    Schema,
    StringField,
    Action,
    AllowAll,
    EdgeDelegate,
    PrivacyRule,
)


class EntTestSubObjectSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("email", 100).not_null().example("vdurmont@gmail.com"),
        ]

    def get_privacy_config(
        self, action: Action
    ) -> PrivacyRule | EdgeDelegate | list[PrivacyRule | EdgeDelegate]:
        return [AllowAll()]
