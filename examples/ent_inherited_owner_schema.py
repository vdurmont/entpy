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

from ent_inherited_test_middle_pattern import EntInheritedTestMiddlePattern
from tiers import Tier


class EntInheritedOwnerSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("owner").serialize(Tier.ITEM),
            EdgeField("inherited", EntInheritedTestMiddlePattern)
            .not_null()
            .serialize(Tier.DETAILED),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
