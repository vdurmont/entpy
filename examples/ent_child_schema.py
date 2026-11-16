from entpy import (
    Field,
    Schema,
    StringField,
    EdgeField,
    Action,
    AllowAll,
    EdgeDelegate,
    PrivacyRule,
)
from ent_parent_schema import EntParentSchema
from tiers import Tier


class EntChildSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("parent", EntParentSchema).not_null().serialize(Tier.ITEM),
            StringField("name", 100)
            .not_null()
            .example("Benjamin")
            .serialize(Tier.ITEM),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
