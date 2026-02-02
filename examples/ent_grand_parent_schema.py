from entpy import (
    Field,
    Schema,
    StringField,
    Action,
    AllowAll,
    EdgeDelegate,
    PrivacyRule,
)


class EntGrandParentSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("Anne"),
        ]

    def get_privacy_config(self, action: Action) -> PrivacyRule | EdgeDelegate | list[PrivacyRule | EdgeDelegate]:
        return [AllowAll()]
