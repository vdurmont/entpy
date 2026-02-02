from entpy import (
    Action,
    EdgeDelegate,
    EdgeField,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)

from ent_delegating_child_schema import EntDelegatingChildSchema


class EntDelegatingGrandchildSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            EdgeField("delegating_child", EntDelegatingChildSchema).not_null(),
            StringField("name", 100).not_null().example("Delegating Grandchild"),
        ]

    def get_privacy_config(self, action: Action) -> PrivacyRule | EdgeDelegate | list[PrivacyRule | EdgeDelegate]:
        # Delegate privacy evaluation to the child (which itself delegates to parent)
        return EdgeDelegate(edge_name="delegating_child")
