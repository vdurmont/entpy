from entpy import EntTrigger
from evc import ExampleViewerContext
from generated.ent_credential import EntCredentialModel
from generated.ent_policy import EntPolicyMutator


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-")


class CredentialTrigger(EntTrigger[ExampleViewerContext, EntCredentialModel]):
    """Exercises trigger capabilities:

    - computes the stored `slug` field from the name (on create and on update),
    - co-creates a default policy on create,
    - aborts the whole mutation (create or update) when the name is "boom".
    """

    async def gen_on_create(
        self, vc: ExampleViewerContext, model: EntCredentialModel
    ) -> EntCredentialModel:
        if model.name == "boom":
            raise ValueError("credential name 'boom' is not allowed")

        # Compute a stored field on the credential being created.
        model.slug = _slugify(model.name)

        # Co-create a default policy referencing the credential.
        await EntPolicyMutator.create(
            vc=vc,
            credential_id=model.id,
            name="default",
        ).gen_savex()

        return model

    async def gen_on_update(
        self,
        vc: ExampleViewerContext,
        old_model: EntCredentialModel,
        new_model: EntCredentialModel,
    ) -> EntCredentialModel:
        if new_model.name == "boom":
            raise ValueError("credential name 'boom' is not allowed")

        # Recompute the stored slug when the name changed.
        if old_model.name != new_model.name:
            new_model.slug = _slugify(new_model.name)

        return new_model
