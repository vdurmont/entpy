from entpy import (
    Field,
    Schema,
    StringField,
    EdgeField,
    Action,
    AllowAll,
    ComputedApiFieldsConfig,
    ImportedObject,
    EdgeDelegate,
    PrivacyRule,
)
from computed_models import ChildComputedDetailed, ChildComputedItem
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

    def get_computed_api_fields_config(self) -> ComputedApiFieldsConfig:
        return ComputedApiFieldsConfig(
            models={Tier.ITEM: ChildComputedItem, Tier.DETAILED: ChildComputedDetailed},
            resolver=ImportedObject(
                module="resolvers", name="gen_child_computed_api_fields"
            ),
        )

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
