from entpy import (
    Action,
    Decision,
    EdgeDelegate,
    Ent,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)

from evc import ExampleViewerContext


class AlwaysPass(PrivacyRule):
    """A rule that always returns PASS."""

    async def gen_evaluate(self, vc: ExampleViewerContext, ent: Ent) -> Decision:
        return Decision.PASS


class AlwaysDeny(PrivacyRule):
    """A rule that always returns DENY."""

    async def gen_evaluate(self, vc: ExampleViewerContext, ent: Ent) -> Decision:
        return Decision.DENY


class EntPassThenDenySchema(Schema):
    """Entity that tests PASS behavior - first rule passes, second rule denies."""

    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("Pass Then Deny Entity"),
        ]

    def get_privacy_config(
        self, action: Action
    ) -> PrivacyRule | EdgeDelegate | list[PrivacyRule | EdgeDelegate]:
        # First rule passes, second rule denies
        return [AlwaysPass(), AlwaysDeny()]
