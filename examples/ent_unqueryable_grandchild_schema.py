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

from ent_unqueryable_middle_pattern import EntUnqueryableMiddlePattern


class EntUnqueryableGrandchildSchema(Schema):
    """Implements the queryable middle pattern, and through it the unqueryable
    root."""

    def get_patterns(self) -> list[Pattern]:
        return [EntUnqueryableMiddlePattern()]

    def get_fields(self) -> list[Field]:
        return [
            StringField("detail", 100).example("a detail"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
