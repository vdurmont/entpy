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


class EntUnqueryableSiblingSchema(Schema):
    """A second implementation, so the pattern is the multi-implementation
    shape a view would normally union rather than a degenerate one.

    It also lives in a different database schema than its sibling, which an
    interface-only pattern is allowed to span."""

    def get_patterns(self) -> list[Pattern]:
        return [EntUnqueryablePattern()]

    def get_fields(self) -> list[Field]:
        return [
            StringField("other_note", 100).example("another note"),
        ]

    @classmethod
    def get_table_schema(cls) -> str | None:
        return "other"

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
