from entpy import (
    Field,
    Schema,
    StringField,
    Action,
    AllowAll,
    EdgeDelegate,
    PrivacyRule,
)

from tiers import Tier


class EntGrandParentSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("Anne").serialize(Tier.ITEM),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
