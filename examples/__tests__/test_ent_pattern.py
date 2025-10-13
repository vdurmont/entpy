from sqlalchemy.ext.asyncio import AsyncSession

from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)
from generated.ent_test_object2 import (
    EntTestObject2Example,
)
from generated.ent_test_thing import IEntTestThing
from evc import ExampleViewerContext


async def test_gen_from_pattern(
    db_session: AsyncSession, vc: ExampleViewerContext
) -> None:
    ent = await EntTestObjectExample.gen_create(vc)

    result = await IEntTestThing.gen(vc, ent.id)

    assert result is not None, "gen should not return None for a valid ID"
    assert isinstance(result, EntTestObject), "we should get the right type"


async def test_genx_from_pattern(
    db_session: AsyncSession, vc: ExampleViewerContext
) -> None:
    ent = await EntTestObjectExample.gen_create(vc)

    result = await IEntTestThing.genx(vc, ent.id)

    assert isinstance(result, EntTestObject), "we should get the right type"


async def test_query_across_schemas(
    db_session: AsyncSession, vc: ExampleViewerContext
) -> None:
    _red = await EntTestObjectExample.gen_create(vc=vc, a_good_thing="red")
    blue = await EntTestObjectExample.gen_create(vc=vc, a_good_thing="blue")
    brown = await EntTestObject2Example.gen_create(vc=vc, a_good_thing="brown")
    _yellow = await EntTestObject2Example.gen_create(vc=vc, a_good_thing="yellow")

    # ents = (
    #     await IEntTestThing.query(vc)
    #     .where(EntTestThingView.a_good_thing.startswith("b"))
    #     .order_by(EntTestThingView.id.desc())
    #     .gen()
    # )

    # assert len(ents) == 2
    # ids = [ent.id for ent in ents]
    # assert ids[0] == brown.id
    # assert ids[1] == blue.id

    assert False, "Write the test bruh"
