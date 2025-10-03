import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from examples.generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)
from examples.generated.ent_test_sub_object import EntTestSubObject  # noqa: F401
from framework.viewer_context import ViewerContext


async def test_creation(db_session: AsyncSession, vc: ViewerContext) -> None:
    ent = await EntTestObjectMutator.create(
        vc=vc,
        username="vdurmont",
        firstname="Vincent",
        required_sub_object_id=uuid.uuid4(),
    ).gen_savex()

    assert ent is not None, "create should create the ent"
    assert ent.firstname == "Vincent"

    ent = await EntTestObject.genx(vc, ent.id)

    assert ent is not None, "created ents should be loadable"
    assert ent.firstname == "Vincent"


async def test_update(db_session: AsyncSession, vc: ViewerContext) -> None:
    name = "Chris"

    ent = await EntTestObjectExample.gen_create(vc=vc)

    assert ent.firstname != name, "In the setup, we have a different name."

    mut = EntTestObjectMutator.update(vc, ent)
    mut.firstname = name
    ent = await mut.gen_savex()

    assert ent.firstname == name, "Name should have been updated"


async def test_deletion(db_session: AsyncSession, vc: ViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc=vc)

    await EntTestObjectMutator.delete(vc, ent).gen_save()

    reloaded_ent = await EntTestObject.gen(vc, ent.id)

    assert reloaded_ent is None, "Ent should have been deleted"
