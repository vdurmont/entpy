"""`include_soft_deleted` is remembered by the ent it loaded and followed across edges.

Reading a soft-deleted ent is a deliberate act -- an admin screen, a restore
flow, an audit -- and the ents it reaches through are usually soft-deleted too.
Passing the flag only to the first `gen()` would make every hop after it fail,
so the ent stores what it was loaded with and hands it to the edges it fetches.

The flag only lifts the query filter. These examples also prepend
`DenyIfSoftDeleted` to their read privacy, so every read below uses the test VC
that outranks it.
"""

import pytest
from entpy.framework.errors import EntNotFoundError
from evc import ExampleTestViewerContext, ExampleViewerContext

from generated.ent_child import EntChild, EntChildExample
from generated.ent_grand_parent import EntGrandParentMutator
from generated.ent_parent import EntParentMutator
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)
from generated.ent_test_object5 import EntTestObject5Mutator
from generated.ent_test_sub_object import (
    EntTestSubObjectExample,
    EntTestSubObjectMutator,
)
from generated.ent_test_thing import IEntTestThing


async def test_required_edge_hidden_when_target_soft_deleted(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc)
    parent = await child.gen_parent()
    await EntParentMutator.soft_delete(vc, parent).gen_save()

    test_vc = ExampleTestViewerContext()
    reloaded = await EntChild.genx(test_vc, child.id)
    with pytest.raises(EntNotFoundError):
        await reloaded.gen_parent()


async def test_required_edge_follows_stored_include_soft_deleted(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc)
    parent = await child.gen_parent()
    await EntParentMutator.soft_delete(vc, parent).gen_save()

    test_vc = ExampleTestViewerContext()
    reloaded = await EntChild.genx(test_vc, child.id, include_soft_deleted=True)
    found = await reloaded.gen_parent()
    assert found.id == parent.id
    assert found.soft_deleted_at is not None


async def test_stored_include_soft_deleted_is_transitive(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc)
    parent = await child.gen_parent()
    grand_parent = await parent.gen_grand_parent()
    await EntGrandParentMutator.soft_delete(vc, grand_parent).gen_save()

    test_vc = ExampleTestViewerContext()
    reloaded = await EntChild.genx(test_vc, child.id, include_soft_deleted=True)
    found = await (await reloaded.gen_parent()).gen_grand_parent()
    assert found.id == grand_parent.id
    assert found.soft_deleted_at is not None


async def test_nullable_edge_follows_stored_include_soft_deleted(
    vc: ExampleViewerContext,
) -> None:
    sub_object = await EntTestSubObjectExample.gen_create(vc)
    obj = await EntTestObjectExample.gen_create(
        vc, optional_sub_object_id=sub_object.id
    )
    await EntTestSubObjectMutator.soft_delete(vc, sub_object).gen_save()

    test_vc = ExampleTestViewerContext()
    hidden = await EntTestObject.genx(test_vc, obj.id)
    assert await hidden.gen_optional_sub_object() is None

    reloaded = await EntTestObject.genx(test_vc, obj.id, include_soft_deleted=True)
    found = await reloaded.gen_optional_sub_object()
    assert found is not None
    assert found.id == sub_object.id


async def test_unique_lookup_propagates_to_edges(vc: ExampleViewerContext) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    obj5 = await obj.gen_obj5()
    await EntTestObject5Mutator.soft_delete(vc, obj5).gen_save()

    test_vc = ExampleTestViewerContext()
    reloaded = await EntTestObject.genx_from_username(
        test_vc, obj.username, include_soft_deleted=True
    )
    assert reloaded is not None
    found = await reloaded.gen_obj5()
    assert found.id == obj5.id


async def test_unique_cache_is_keyed_on_include_soft_deleted(
    vc: ExampleViewerContext,
) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    username = obj.username
    await EntTestObjectMutator.soft_delete(vc, obj).gen_save()

    test_vc = ExampleTestViewerContext()
    assert (
        await EntTestObject.gen_from_username(
            test_vc, username, include_soft_deleted=True
        )
        is not None
    )
    assert await EntTestObject.gen_from_username(test_vc, username) is None


async def test_pattern_gen_propagates_to_edges(vc: ExampleViewerContext) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    obj5 = await obj.gen_obj5()
    await EntTestObject5Mutator.soft_delete(vc, obj5).gen_save()

    test_vc = ExampleTestViewerContext()
    reloaded = await IEntTestThing.genx(test_vc, obj.id, include_soft_deleted=True)
    found = await reloaded.gen_obj5()
    assert found.id == obj5.id


async def test_query_with_soft_deleted_propagates_to_edges(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc)
    parent = await child.gen_parent()
    await EntParentMutator.soft_delete(vc, parent).gen_save()

    test_vc = ExampleTestViewerContext()
    ents = await EntChild.query(test_vc).where(EntChild.m.id == child.id).gen()
    with pytest.raises(EntNotFoundError):
        await ents[0].gen_parent()

    ents = (
        await EntChild.query(test_vc)
        .where(EntChild.m.id == child.id)
        .with_soft_deleted()
        .gen()
    )
    found = await ents[0].gen_parent()
    assert found.id == parent.id


async def test_pattern_gen_by_ids_propagates_to_edges(
    vc: ExampleViewerContext,
) -> None:
    obj = await EntTestObjectExample.gen_create(vc)
    obj5 = await obj.gen_obj5()
    await EntTestObject5Mutator.soft_delete(vc, obj5).gen_save()

    test_vc = ExampleTestViewerContext()
    by_id = await IEntTestThing.gen_by_ids(test_vc, [obj.id], include_soft_deleted=True)
    found = await by_id[obj.id].gen_obj5()
    assert found.id == obj5.id
