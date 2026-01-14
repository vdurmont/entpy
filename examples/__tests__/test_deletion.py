from evc import ExampleTestViewerContext, ExampleViewerContext
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)


async def test_hard_delete(vc: ExampleViewerContext) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    await EntTestObjectMutator.hard_delete(vc, obj).gen_save()
    res = await EntTestObject.gen(vc, obj.id)
    assert res is None, "Ent should be deleted"


async def test_soft_delete_with_regular_vc(vc: ExampleViewerContext) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    await EntTestObjectMutator.soft_delete(vc, obj).gen_save()

    # Cannot read with regular vc
    res = await EntTestObject.gen(vc, obj.id)
    assert res is None, "Ent should be soft deleted"


async def test_soft_delete_with_super_vc(vc: ExampleViewerContext) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    await EntTestObjectMutator.soft_delete(vc, obj).gen_save()

    # Can still read with test vc
    test_vc = ExampleTestViewerContext()
    res = await EntTestObject.gen(test_vc, obj.id)
    assert res is not None, "Soft deleted Ent should be readable by test vc"
    assert res.soft_deleted_at is not None


async def test_soft_delete_default_queries_with_regular_vc(
    vc: ExampleViewerContext,
) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    await EntTestObjectMutator.soft_delete(vc, obj).gen_save()

    # Don't get it by default in queries with regular vc
    objs = await EntTestObject.query(vc).gen()
    assert len(objs) == 0, "Query should filter out the soft deleted ents"
    count = await EntTestObject.query(vc).gen_count_NO_PRIVACY()
    assert count == 0


async def test_soft_delete_specific_queries_with_regular_vc(
    vc: ExampleViewerContext,
) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    await EntTestObjectMutator.soft_delete(vc, obj).gen_save()

    # Don't get it in queries with regular vc even if requested
    objs = await EntTestObject.query(vc).with_soft_deleted().gen()
    assert len(objs) == 0, (
        "Query should never return the soft deleted ents with regular vc"
    )
    count = await EntTestObject.query(vc).with_soft_deleted().gen_count_NO_PRIVACY()
    assert count == 0


async def test_soft_delete_default_queries_with_super_vc(
    vc: ExampleViewerContext,
) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    await EntTestObjectMutator.soft_delete(vc, obj).gen_save()

    # Don't get it by default in queries with test vc
    test_vc = ExampleTestViewerContext()
    objs = await EntTestObject.query(test_vc).gen()
    assert len(objs) == 0, "Query should filter out the soft deleted ents"
    count = await EntTestObject.query(test_vc).gen_count_NO_PRIVACY()
    assert count == 0


async def test_soft_delete_specific_queries_with_super_vc(
    vc: ExampleViewerContext,
) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    await EntTestObjectMutator.soft_delete(vc, obj).gen_save()

    # Get it in queries with test vc if requested
    test_vc = ExampleTestViewerContext()
    objs = await EntTestObject.query(test_vc).with_soft_deleted().gen()
    assert len(objs) == 1, "Query should return the soft deleted ents when requested"
    assert objs[0].id == obj.id
    count = (
        await EntTestObject.query(test_vc).with_soft_deleted().gen_count_NO_PRIVACY()
    )
    assert count == 1
