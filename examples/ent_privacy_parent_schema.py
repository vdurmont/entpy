from entpy import (
    Action,
    EdgeDelegate,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)

from rules import AllowIfOmniscientViewerContext, AllowIfTestViewerContext


class EntPrivacyParentSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("Privacy Parent"),
        ]

    def get_privacy_config(self, action: Action) -> list[PrivacyRule] | EdgeDelegate:
        # Allow TestViewerContext and OmniscientViewerContext, deny others
        return [
            AllowIfTestViewerContext(),
            AllowIfOmniscientViewerContext(),
        ]
