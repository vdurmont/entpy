from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)
from entpy.framework.pattern import Pattern

from ent_unqueryable_pattern import EntUnqueryablePattern


class EntUnqueryableChildSchema(Schema):
    def get_patterns(self) -> list[Pattern]:
        return [EntUnqueryablePattern()]

    def get_fields(self) -> list[Field]:
        return [
            StringField("note", 100).example("a note"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
