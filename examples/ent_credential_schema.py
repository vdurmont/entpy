from typing import Any

from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
    EntTrigger,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)


class EntCredentialSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("My Credential"),
            StringField("slug", 100).example("my-credential"),
        ]

    def get_triggers(self) -> list[EntTrigger[Any, Any]]:
        from credential_triggers import CredentialTrigger

        return [CredentialTrigger()]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
