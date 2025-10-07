from sqlalchemy.ext.asyncio import AsyncSession

from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)
from generated.ent_test_sub_object import EntTestSubObject  # noqa: F401
from generated.ent_test_thing import IEntTestThing
from entpy import ViewerContext


async def test_gen_from_pattern(db_session: AsyncSession, vc: ViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc)

    result = await IEntTestThing.gen(vc, ent.id)

    assert result is not None, "gen should not return None for a valid ID"
    assert isinstance(result, EntTestObject), "we should get the right type"


async def test_genx_from_pattern(db_session: AsyncSession, vc: ViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc)

    result = await IEntTestThing.genx(vc, ent.id)

    assert isinstance(result, EntTestObject), "we should get the right type"
