from entpy.framework.model import ModelMixin
from entpy.framework.viewer_context import ViewerContext


class EntTrigger[VC: ViewerContext, ENTMODEL: ModelMixin]:
    """
    A trigger runs during a mutation, *before* the privacy check (and therefore
    before the row is flushed). Running first is deliberate: what a trigger
    produces is what the privacy rules evaluate, so a trigger cannot shape a
    value in a way that bypasses authorization.

    Subclass it bound to your viewer context and generated model, e.g.
    `EntCredentialTrigger(EntTrigger[ExampleViewerContext, EntCredentialModel])`,
    so the models handed to each hook are fully typed.

    Because triggers run inside the mutation (and inside the caller's
    transaction), they can:

    - Abort the whole mutation by raising. Nothing is committed.
    - Compute stored fields on the model (see per-hook notes below).
    - Make related transactional changes by calling other mutators -- e.g.
      co-create a child on create, or cascade updates/deletes to related ents on
      delete. The whole thing is atomic: everything is authorized before commit,
      and if anything raises the caller's transaction rolls back.

    Per-hook semantics:

    - `gen_on_create(vc, model)` returns the model to persist. `model` is the row
      being created; shape it (or return a replacement) and return it. The
      returned model is validated, privacy-checked and written -- so this is
      where you compute stored fields (`model.slug = slugify(model.name)`).
    - `gen_on_update(vc, old_model, new_model)` returns the model to persist.
      `old_model` is a fresh snapshot of the current row, for comparison (each
      trigger gets its own copy, so mutating it has no effect). `new_model` is a
      working copy with the caller's changes applied; shape it and return it, and
      it is privacy-checked and persisted
      (`if old_model.name != new_model.name: new_model.slug = ...`).
    - `gen_on_delete(vc, model, is_soft_delete)` runs before the delete; `model`
      is the row being removed, as read-only context for cascades. It returns
      nothing.

    Triggers must only perform work that is safe to roll back: shape the model,
    make related transactional changes, or abort. Do NOT perform irreversible or
    external side effects (emails, third-party API calls) in a trigger -- it runs
    before the mutation is authorized, so a later denial would not undo them.
    Those belong in an observer, which runs after commit.

    Triggers receive the caller's viewer context. A trigger that needs elevated
    permissions (e.g. to co-create an ent the caller could not create directly)
    should construct its own viewer context and ignore the one passed in.

    Override only the actions you care about; the rest are no-ops.
    """

    async def gen_on_create(self, vc: VC, model: ENTMODEL) -> ENTMODEL:
        return model

    async def gen_on_update(
        self, vc: VC, old_model: ENTMODEL, new_model: ENTMODEL
    ) -> ENTMODEL:
        return new_model

    async def gen_on_delete(
        self, vc: VC, model: ENTMODEL, is_soft_delete: bool
    ) -> None:
        pass
