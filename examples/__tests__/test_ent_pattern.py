from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)
from generated.ent_test_object2 import (
    EntTestObject2Example,
)
from generated.ent_test_thing import IEntTestThing
from generated.ent_test_thing_view import EntTestThingView
from evc import ExampleViewerContext


async def test_gen_from_pattern(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc)

    result = await IEntTestThing.gen(vc, ent.id)

    assert result is not None, "gen should not return None for a valid ID"
    assert isinstance(result, EntTestObject), "we should get the right type"


async def test_genx_from_pattern(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc)

    result = await IEntTestThing.genx(vc, ent.id)

    assert isinstance(result, EntTestObject), "we should get the right type"


async def test_query_across_schemas(vc: ExampleViewerContext) -> None:
    red = await EntTestObjectExample.gen_create(vc=vc, a_good_thing="red")
    blue = await EntTestObjectExample.gen_create(vc=vc, a_good_thing="blue")
    brown = await EntTestObject2Example.gen_create(vc=vc, a_good_thing="brown")
    _yellow = await EntTestObject2Example.gen_create(vc=vc, a_good_thing="yellow")

    ents = (
        await IEntTestThing.query_ent_test_thing(vc)
        .where(EntTestThingView.a_good_thing.startswith("b"))
        .order_by(EntTestThingView.id.desc())
        .gen()
    )

    assert len(ents) == 2
    ids = [ent.id for ent in ents]
    assert ids[0] == brown.id
    assert ids[1] == blue.id

    ent = (
        await IEntTestThing.query_ent_test_thing(vc)
        .where(EntTestThingView.a_good_thing.startswith("r"))
        .genx_first()
    )

    assert ent.id == red.id

    count = (
        await IEntTestThing.query_ent_test_thing_count(vc)
        .where(EntTestThingView.a_good_thing.startswith("y"))
        .gen_NO_PRIVACY()
    )
    assert count == 1

    count = (
        await IEntTestThing.query_ent_test_thing_count(vc)
        .where(EntTestThingView.a_good_thing.startswith("b"))
        .gen_NO_PRIVACY()
    )
    assert count == 2

    count = (
        await IEntTestThing.query_ent_test_thing_count(vc)
        .where(EntTestThingView.a_good_thing.startswith("v"))
        .gen_NO_PRIVACY()
    )
    assert count == 0
