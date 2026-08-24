from entpy import (
    Action,
    DenyAll,
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

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        # Allow TestViewerContext and OmniscientViewerContext, deny others
        if action in (Action.READ, Action.CREATE, Action.HARD_DELETE):
            return [
                AllowIfTestViewerContext(),
                AllowIfOmniscientViewerContext(),
            ]
        return [DenyAll()]
