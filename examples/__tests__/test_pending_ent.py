from unittest.mock import AsyncMock, patch

from evc import ExampleViewerContext
from generated.ent_user import (
    EntUser,
    EntUserExample,
    EntUserMutator,
    EntUserPending,
)


async def test_create_passes_pending_ent(vc: ExampleViewerContext) -> None:
    with patch.object(
        EntUser, "gen_evaluate_privacy", new_callable=AsyncMock
    ) as mock_privacy:
        from entpy.framework.decision import Decision

        mock_privacy.return_value = Decision.ALLOW

        await EntUserMutator.create(
            vc=vc,
            email="alice@example.com",
            name="Alice",
        ).gen_savex()

        mock_privacy.assert_called_once()
        call_kwargs = mock_privacy.call_args
        pending_ent = call_kwargs.kwargs["pending_ent"]

        assert isinstance(pending_ent, EntUserPending)
        assert pending_ent.name == "Alice"
        assert pending_ent.email == "alice@example.com"


async def test_update_pending_ent_has_new_values(vc: ExampleViewerContext) -> None:
    bob = await EntUserExample.gen_create(vc, name="Bob", email="bob@example.com")
    assert bob.name == "Bob"

    with patch.object(
        EntUser, "gen_evaluate_privacy", new_callable=AsyncMock
    ) as mock_privacy:
        from entpy.framework.decision import Decision

        mock_privacy.return_value = Decision.ALLOW

        mut = EntUserMutator.update(vc, bob)
        mut.name = "John"
        await mut.gen_savex()

        mock_privacy.assert_called_once()
        call_kwargs = mock_privacy.call_args
        pending_ent = call_kwargs.kwargs["pending_ent"]

        assert isinstance(pending_ent, EntUserPending)
        assert pending_ent.name == "John"
        assert pending_ent.email == "bob@example.com"


async def test_update_ent_still_has_old_values(vc: ExampleViewerContext) -> None:
    bob = await EntUserExample.gen_create(vc, name="Bob", email="bob@example.com")

    captured_ent_name = None

    async def capture_ent_name(self, *, vc, action, pending_ent=None, **kwargs):
        nonlocal captured_ent_name
        from entpy.framework.decision import Decision

        captured_ent_name = bob.name
        return Decision.ALLOW

    with patch.object(EntUser, "gen_evaluate_privacy", new=capture_ent_name):
        mut = EntUserMutator.update(vc, bob)
        mut.name = "John"
        await mut.gen_savex()

    assert captured_ent_name == "Bob"


async def test_delete_passes_pending_ent(vc: ExampleViewerContext) -> None:
    bob = await EntUserExample.gen_create(vc, name="Bob", email="bob@example.com")

    with patch.object(
        EntUser, "gen_evaluate_privacy", new_callable=AsyncMock
    ) as mock_privacy:
        from entpy.framework.decision import Decision

        mock_privacy.return_value = Decision.ALLOW

        await EntUserMutator.soft_delete(vc, bob).gen_save()

        mock_privacy.assert_called_once()
        call_kwargs = mock_privacy.call_args
        pending_ent = call_kwargs.kwargs["pending_ent"]

        assert isinstance(pending_ent, EntUserPending)
        assert pending_ent.name == "Bob"
        assert pending_ent.email == "bob@example.com"
