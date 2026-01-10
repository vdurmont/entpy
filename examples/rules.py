from entpy import Decision, Ent, PrivacyRule

from evc import (
    ExampleOmniscientViewerContext,
    ExampleTestViewerContext,
    ExampleViewerContext,
)


class AllowIfTestViewerContext(PrivacyRule):
    async def gen_evaluate(self, vc: ExampleViewerContext, ent: Ent) -> Decision:
        return (
            Decision.ALLOW
            if isinstance(vc, ExampleTestViewerContext)
            else Decision.PASS
        )


class AllowIfOmniscientViewerContext(PrivacyRule):
    async def gen_evaluate(self, vc: ExampleViewerContext, ent: Ent) -> Decision:
        return (
            Decision.ALLOW
            if isinstance(vc, ExampleOmniscientViewerContext)
            else Decision.PASS
        )


class DenyIfSoftDeleted(PrivacyRule):
    async def gen_evaluate(self, vc: ExampleViewerContext, ent: Ent) -> Decision:
        return Decision.DENY if ent.soft_deleted_at else Decision.PASS
