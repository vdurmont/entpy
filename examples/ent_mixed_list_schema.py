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


class EntMixedListSchema(Schema):
    """Entity that returns a list with both PrivacyRule and EdgeDelegate."""

    def get_fields(self) -> list[Field]:
        return [
            EdgeField("privacy_parent", EntPrivacyParentSchema).not_null(),
            StringField("name", 100).not_null().example("Mixed List Entity"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        # Return a mixed list: first check OmniscientViewerContext rule,
        # if it passes, delegate to the parent
        return [
            AllowIfOmniscientViewerContext(),
            EdgeDelegate(edge_name="privacy_parent"),
        ]
