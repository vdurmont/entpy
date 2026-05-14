from entpy import Decision, Ent, EntPending, PrivacyRule

from evc import (
    ExampleOmniscientViewerContext,
    ExampleTestViewerContext,
    ExampleViewerContext,
)


class AllowIfTestViewerContext(PrivacyRule):
    async def gen_evaluate(
        self, vc: ExampleViewerContext, ent: Ent, pending_ent: EntPending | None = None
    ) -> Decision:
        return (
            Decision.ALLOW
            if isinstance(vc, ExampleTestViewerContext)
            else Decision.PASS
        )


class AllowIfOmniscientViewerContext(PrivacyRule):
    async def gen_evaluate(
        self, vc: ExampleViewerContext, ent: Ent, pending_ent: EntPending | None = None
    ) -> Decision:
        return (
            Decision.ALLOW
            if isinstance(vc, ExampleOmniscientViewerContext)
            else Decision.PASS
        )
