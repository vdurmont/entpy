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
from ent_grand_parent_schema import EntGrandParentSchema


class EntParentSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("grand_parent", EntGrandParentSchema).not_null(),
            StringField("name", 100).not_null().example("Vincent"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
