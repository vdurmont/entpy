from typing import Any, TypeVar, cast

from entpy import (
    Action,
    AllowAll,
    Decision,
    EdgeDelegate,
    Ent,
    EntPending,
    EntTrigger,
    Field,
    PrivacyRule,
    Schema,
    StringField,
)

from evc import ExampleViewerContext

T = TypeVar("T", bound=Ent)
P = TypeVar("P", bound=EntPending)


class DenyIfLevelHigh(PrivacyRule[ExampleViewerContext, T, P]):
    """Denies the action when the (proposed) `level` is "high"."""

    async def gen_evaluate(
        self, vc: ExampleViewerContext, ent: T, pending_ent: P | None = None
    ) -> Decision:
        target = cast(Any, pending_ent if pending_ent is not None else ent)
        return Decision.DENY if target.level == "high" else Decision.ALLOW


class EntGuardedSchema(Schema):
    """Used to prove a trigger-computed field is still subject to privacy: the
    trigger escalates `level` to "high", which CREATE privacy denies."""

    def get_fields(self) -> list[Field]:
        return [
            StringField("level", 20).not_null().example("low"),
        ]

    def get_triggers(self) -> list[EntTrigger[Any, Any]]:
        # Imported lazily: the trigger references the generated model, which
        # imports this schema, so a top-level import would be circular.
        from guarded_triggers import GuardedTrigger

        return [GuardedTrigger()]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        if action == Action.CREATE:
            return [DenyIfLevelHigh()]
        return [AllowAll()]
