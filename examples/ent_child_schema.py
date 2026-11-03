from entpy import (
    Field,
    Schema,
    StringField,
    EdgeField,
    Action,
    AllowAll,
    ComputedApiField,
    ImportedObject,
    EdgeDelegate,
    PrivacyRule,
)
from ent_parent_schema import EntParentSchema
from tiers import Tier


class EntChildSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("parent", EntParentSchema)
            .not_null()
            .serialize(Tier.ITEM, nested=Tier.ITEM),
            StringField("name", 100)
            .not_null()
            .example("Benjamin")
            .serialize(Tier.ITEM),
        ]

    def get_computed_api_fields(self) -> list[ComputedApiField]:
        return [
            ComputedApiField(
                "shout",
                "str",
                resolver=ImportedObject(module="resolvers", name="gen_child_shout"),
            ).serialize(Tier.DETAILED),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
