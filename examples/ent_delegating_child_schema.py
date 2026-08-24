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


class EntDelegatingChildSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("privacy_parent", EntPrivacyParentSchema).not_null(),
            StringField("name", 100).not_null().example("Delegating Child"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        # Delegate privacy evaluation to the parent
        return [
            EdgeDelegate(
                edge_name="privacy_parent",
                actions={Action.UPDATE: Action.CREATE, Action.HARD_DELETE: None},
            )
        ]
