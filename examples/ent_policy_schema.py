from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
    EdgeField,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)

from ent_credential_schema import EntCredentialSchema


class EntPolicySchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("credential", EntCredentialSchema).not_null(),
            StringField("name", 100).not_null().example("default"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
