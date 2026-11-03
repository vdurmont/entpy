from entpy import EdgeField, Field, IntField, Pattern

from ent_grand_parent_schema import EntGrandParentSchema

from ent_inherited_test_top_pattern import EntInheritedTestTopPattern
from tiers import Tier


class EntInheritedTestMiddlePattern(Pattern):
    def get_patterns(self) -> list[Pattern]:
        return [EntInheritedTestTopPattern()]

    def get_fields(self) -> list[Field]:
        return [
            IntField("middle_field")
            .not_null()
            .example(42)
            .serialize(Tier.DETAILED, name="middle"),
            EdgeField("grand_parent", EntGrandParentSchema).serialize(Tier.DETAILED),
        ]
