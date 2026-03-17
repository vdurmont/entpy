from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
    PrivacyRule,
    EdgeField,
    Field,
    Schema,
)
from entpy.framework.pattern import Pattern

from ent_test_object3_schema import EntTestObject3Schema
from ent_other_schema_pattern_pattern import EntOtherSchemaPatternPattern


class EntTestObject4Schema(Schema):
    def get_patterns(self) -> list[Pattern]:
        return [EntOtherSchemaPatternPattern()]

    def get_fields(self) -> list[Field]:
        return [
            EdgeField("other", EntTestObject3Schema),
        ]

    @classmethod
    def get_table_schema(self) -> str | None:
        return "other"

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
