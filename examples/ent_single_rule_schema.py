from entpy import (
    Action,
    EdgeDelegate,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)

from rules import AllowIfTestViewerContext


class EntSingleRuleSchema(Schema):
    """Entity that returns a single PrivacyRule (not a list)."""

    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("Single Rule Entity"),
        ]

    def get_privacy_config(
        self, action: Action
    ) -> PrivacyRule | EdgeDelegate | list[PrivacyRule | EdgeDelegate]:
        # Return a single PrivacyRule, not a list
        return AllowIfTestViewerContext()
