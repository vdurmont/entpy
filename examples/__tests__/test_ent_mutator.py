from sqlalchemy.ext.asyncio import AsyncSession

from examples.generated.ent_test_object import (
    EntTestObject,
    EntTestObjectMutator,
)
from framework.viewer_context import ViewerContext


async def test_create(db_session: AsyncSession, vc: ViewerContext):
    ent = await EntTestObjectMutator.create(vc=vc, firstname="Vincent").gen_savex()

    assert ent is not None, "create should create the ent"
    assert ent.firstname == "Vincent"

    ent = await EntTestObject.genx(vc, ent.id)

    assert ent is not None, "created ents should be loadable"
    assert ent.firstname == "Vincent"
