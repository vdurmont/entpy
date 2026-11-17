from entpy import (
    ComputedApiFieldsConfig,
    DatetimeField,
    Field,
    ImportedObject,
    Pattern,
    StringField,
)

from computed_models import TopComputedItem

from tiers import Tier


class EntInheritedTestTopPattern(Pattern):
    def get_fields(self) -> list[Field]:
        return [
            StringField("base_field", 100)
            .not_null()
            .example("base value")
            .serialize(Tier.ITEM),
            DatetimeField("happened_at").serialize(Tier.ITEM),
        ]

    def get_computed_api_fields_config(self) -> ComputedApiFieldsConfig:
        return ComputedApiFieldsConfig(
            models={Tier.ITEM: TopComputedItem},
            resolver=ImportedObject(
                module="resolvers", name="gen_top_computed_api_fields"
            ),
        )
