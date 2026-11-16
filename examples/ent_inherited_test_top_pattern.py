from entpy import DatetimeField, Field, Pattern, StringField

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
