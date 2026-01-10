from ent_test_thing_pattern import ThingStatus
from evc import ExampleViewerContext
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)
from generated.ent_test_object2 import (
    EntTestObject2Example,
)
from generated.ent_test_object5 import EntTestObject5Example
from generated.ent_test_thing import IEntTestThing, IEntTestThingMutator
from generated.ent_test_thing_view import EntTestThingView


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
        await IEntTestThing.query_ent_test_thing(vc)
        .where(EntTestThingView.a_good_thing.startswith("y"))
        .gen_count_NO_PRIVACY()
    )
    assert count == 1

    count = (
        await IEntTestThing.query_ent_test_thing(vc)
        .where(EntTestThingView.a_good_thing.startswith("b"))
        .gen_count_NO_PRIVACY()
    )
    assert count == 2

    count = (
        await IEntTestThing.query_ent_test_thing(vc)
        .where(EntTestThingView.a_good_thing.startswith("v"))
        .gen_count_NO_PRIVACY()
    )
    assert count == 0


async def test_query_pattern_edge(vc: ExampleViewerContext) -> None:
    obj5_1 = await EntTestObject5Example.gen_create(vc=vc)
    obj5_2 = await EntTestObject5Example.gen_create(vc=vc)
    obj = await EntTestObjectExample.gen_create(
        vc=vc, obj5_id=obj5_1.id, obj5_opt_id=obj5_2.id
    )
    thing = await IEntTestThing.genx(vc, obj.id)

    non_opt = await thing.gen_obj5()
    opt = await thing.gen_obj5_opt()
    assert non_opt.id == obj5_1.id
    assert opt is not None
    assert opt.id == obj5_2.id


async def test_pattern_mutator_update(vc: ExampleViewerContext) -> None:
    """Test that we can update pattern fields using the pattern's mutator"""
    # Create an ent with initial pattern field values
    ent = await EntTestObjectExample.gen_create(
        vc=vc, a_good_thing="initial value", thing_status=ThingStatus.GOOD
    )

    # Load it as a pattern type
    thing = await IEntTestThing.genx(vc, ent.id)

    # Verify initial values
    assert thing.a_good_thing == "initial value"
    assert thing.thing_status == ThingStatus.GOOD

    # Update using the pattern mutator
    mutator = IEntTestThingMutator.update(vc, thing)
    mutator.a_good_thing = "updated value"
    mutator.thing_status = ThingStatus.BAD

    updated_thing = await mutator.gen_savex()

    # Verify the values were updated
    assert updated_thing.a_good_thing == "updated value"
    assert updated_thing.thing_status == ThingStatus.BAD

    # Reload from database to ensure persistence
    reloaded = await IEntTestThing.genx(vc, ent.id)
    assert reloaded.a_good_thing == "updated value"
    assert reloaded.thing_status == ThingStatus.BAD


async def test_pattern_mutator_delete(vc: ExampleViewerContext) -> None:
    """Test that we can delete ents using the pattern's mutator"""
    # Create an ent
    ent = await EntTestObjectExample.gen_create(vc=vc, a_good_thing="to be deleted")

    # Load it as a pattern type
    thing = await IEntTestThing.genx(vc, ent.id)
    thing_id = thing.id

    # Delete using the pattern mutator
    mutator = IEntTestThingMutator.hard_delete(vc, thing)
    await mutator.gen_save()

    # Verify it was deleted
    deleted_thing = await IEntTestThing.gen(vc, thing_id)
    assert deleted_thing is None, "Ent should be deleted"
