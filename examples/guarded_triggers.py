from entpy import EntTrigger
from evc import ExampleViewerContext
from generated.ent_guarded import EntGuardedModel


class GuardedTrigger(EntTrigger[ExampleViewerContext, EntGuardedModel]):
    async def gen_on_create(
        self, vc: ExampleViewerContext, model: EntGuardedModel
    ) -> EntGuardedModel:
        # Escalate a privacy-relevant field. Because triggers run before the
        # privacy check, this escalation is caught rather than bypassed.
        model.level = "high"
        return model
