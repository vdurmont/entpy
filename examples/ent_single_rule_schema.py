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
    """Entity that returns a list with a single PrivacyRule."""

    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("Single Rule Entity"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        # Return a single PrivacyRule in a list
        return [AllowIfTestViewerContext()]
