import pytest
from entpy import PrivacyError
from evc import ExampleViewerContext
from generated.ent_credential import EntCredential, EntCredentialMutator
from generated.ent_guarded import EntGuarded, EntGuardedMutator
from generated.ent_policy import EntPolicy, EntPolicyModel  # noqa: F401


async def test_trigger_computes_field_on_create(vc: ExampleViewerContext) -> None:
    ent = await EntCredentialMutator.create(vc=vc, name="My Credential").gen_savex()
    assert ent.slug == "my-credential", "trigger should compute the slug from name"


async def test_trigger_co_creates_ent_on_create(vc: ExampleViewerContext) -> None:
    credential = await EntCredentialMutator.create(vc=vc, name="Prod Key").gen_savex()

    policies = await (
        EntPolicy.query(vc).where(EntPolicyModel.credential_id == credential.id).gen()
    )
    assert len(policies) == 1, "trigger should co-create a default policy"
    assert policies[0].name == "default"


async def test_trigger_can_abort_the_mutation(vc: ExampleViewerContext) -> None:
    with pytest.raises(ValueError, match="boom"):
        await EntCredentialMutator.create(vc=vc, name="boom").gen_savex()

    # Nothing should have been persisted (neither the credential nor a policy).
    assert await EntCredential.query(vc).gen_count() == 0
    assert await EntPolicy.query(vc).gen_count() == 0


async def test_trigger_can_abort_update(vc: ExampleViewerContext) -> None:
    ent = await EntCredentialMutator.create(vc=vc, name="My Credential").gen_savex()

    mut = EntCredentialMutator.update(vc, ent)
    mut.name = "boom"
    with pytest.raises(ValueError, match="boom"):
        await mut.gen_savex()

    reloaded = await EntCredential.genx(vc, ent.id)
    assert reloaded.name == "My Credential", "aborted update should not persist"


async def test_trigger_computes_field_on_update(vc: ExampleViewerContext) -> None:
    ent = await EntCredentialMutator.create(vc=vc, name="My Credential").gen_savex()
    assert ent.slug == "my-credential"

    mut = EntCredentialMutator.update(vc, ent)
    mut.name = "Renamed Credential"
    ent = await mut.gen_savex()

    assert ent.name == "Renamed Credential"
    assert ent.slug == "renamed-credential", "update trigger's slug should persist"

    # Confirm it actually reached the database.
    reloaded = await EntCredential.genx(vc, ent.id)
    assert reloaded.slug == "renamed-credential"


async def test_trigger_computed_field_is_privacy_checked(
    vc: ExampleViewerContext,
) -> None:
    # The caller passes an allowed value, but the trigger escalates `level` to
    # "high". Because triggers run before the privacy check, the escalated value
    # is what privacy sees, so the create is denied rather than bypassed.
    with pytest.raises(PrivacyError):
        await EntGuardedMutator.create(vc=vc, level="low").gen_savex()

    assert await EntGuarded.query(vc).gen_count() == 0, "nothing should persist"
