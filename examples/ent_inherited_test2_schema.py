from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
    Field,
    Pattern,
    PrivacyRule,
    Schema,
    StringField,
)

from ent_inherited_test_middle_pattern import EntInheritedTestMiddlePattern


class EntInheritedTest2Schema(Schema):
    def get_patterns(self) -> list[Pattern]:
        return [EntInheritedTestMiddlePattern()]

    def get_fields(self) -> list[Field]:
        return [StringField("schema_field", 100).not_null().example("schema value")]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]

    @classmethod
    def get_table_schema(self) -> str:
        return "other"
