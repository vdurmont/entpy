from entpy import (
    Action,
    EdgeDelegate,
    EdgeField,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)

from ent_privacy_parent_schema import EntPrivacyParentSchema
from rules import AllowIfOmniscientViewerContext


class EntDelegateThenRuleSchema(Schema):
    """Entity that delegates first, then has a fallback rule.

    This demonstrates that EdgeDelegate with default_to_deny=False returns PASS
    when no rules match, allowing subsequent rules to be evaluated.
    """

    def get_fields(self) -> list[Field]:
        return [
            EdgeField("privacy_parent", EntPrivacyParentSchema).not_null(),
            StringField("name", 100).not_null().example("Delegate Then Rule Entity"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        # First, delegate to parent (which only allows Test/Omniscient viewers)
        # If delegation returns PASS, try the Omniscient rule as fallback
        return [
            EdgeDelegate(edge_name="privacy_parent"),
            AllowIfOmniscientViewerContext(),
        ]
