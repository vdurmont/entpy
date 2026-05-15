from typing import TypeVar

from entpy import Decision, Ent, EntPending, PrivacyRule

from evc import (
    ExampleOmniscientViewerContext,
    ExampleTestViewerContext,
    ExampleViewerContext,
)

T = TypeVar("T", bound=Ent)
P = TypeVar("P", bound=EntPending)


class AllowIfTestViewerContext(PrivacyRule[ExampleViewerContext, T, P]):
    async def gen_evaluate(
        self, vc: ExampleViewerContext, ent: T, pending_ent: P | None = None
    ) -> Decision:
        return (
            Decision.ALLOW
            if isinstance(vc, ExampleTestViewerContext)
            else Decision.PASS
        )


class AllowIfOmniscientViewerContext(PrivacyRule[ExampleViewerContext, T, P]):
    async def gen_evaluate(
        self, vc: ExampleViewerContext, ent: T, pending_ent: P | None = None
    ) -> Decision:
        return (
            Decision.ALLOW
            if isinstance(vc, ExampleOmniscientViewerContext)
            else Decision.PASS
        )
