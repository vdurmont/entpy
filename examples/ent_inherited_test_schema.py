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


class EntInheritedTestSchema(Schema):
    def get_patterns(self) -> list[Pattern]:
        # Include middle pattern which itself inherits from base pattern
        # Also include base pattern to satisfy code generator requirements
        return [EntInheritedTestMiddlePattern()]

    def get_fields(self) -> list[Field]:
        return [StringField("schema_field", 100).not_null().example("schema value")]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
