from entpy import Decision, Ent, PrivacyRule

from evc import ExampleTestViewerContext, ExampleViewerContext


class AllowIfTestViewerContext(PrivacyRule):
    async def gen_evaluate(self, vc: ExampleViewerContext, ent: Ent) -> Decision:
        return (
            Decision.ALLOW
            if isinstance(vc, ExampleTestViewerContext)
            else Decision.PASS
        )
