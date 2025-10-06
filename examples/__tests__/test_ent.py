import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from examples.generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)
from examples.generated.ent_test_sub_object import EntTestSubObject  # noqa: F401
from framework import ViewerContext


async def test_ent_test_object_gen_with_existing_model(
    db_session: AsyncSession, vc: ViewerContext
) -> None:
    ent = await EntTestObjectExample.gen_create(vc, firstname="Vincent")

    result = await EntTestObject.gen(vc, ent.id)

    assert result is not None, "gen should not return None for a valid ID"
    assert result.firstname == "Vincent"


async def test_ent_test_object_gen_with_unknown_model(
    db_session: AsyncSession, vc: ViewerContext
) -> None:
    ent_id = uuid.uuid4()
    result = await EntTestObject.gen(vc, ent_id)

    assert result is None, "gen should return None for an invalid ID"


async def test_ent_test_object_genx_with_existing_model(
    db_session: AsyncSession, vc: ViewerContext
) -> None:
    ent = await EntTestObjectExample.gen_create(vc, firstname="Vincent")

    result = await EntTestObject.genx(vc, ent.id)

    assert result is not None, "genx should not return None for a valid ID"
    assert result.firstname == "Vincent"


async def test_ent_test_object_genx_with_unknown_model(
    db_session: AsyncSession, vc: ViewerContext
) -> None:
    ent_id = uuid.uuid4()
    with pytest.raises(ValueError):
        await EntTestObject.genx(vc, ent_id)


async def test_edges_work_well(db_session: AsyncSession, vc: ViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc, firstname="Vincent")

    # Check required
    assert (
        ent.required_sub_object_id is not None
    ), "We should be able to access the required edge's ID"
    req_edge = await ent.gen_required_sub_object()
    assert req_edge is not None, "We should be able to load the required edge"

    # Check optional, but example generated
    assert ent.optional_sub_object_id is not None, "Example generates a sub object"
    opt_edge = await ent.gen_optional_sub_object()
    assert opt_edge is not None, "We should be able to load the optional edge"

    # Check optional, but example cancelled
    assert (
        ent.optional_sub_object_no_ex_id is None
    ), "Example does not generate a sub object"
    opt_edge_2 = await ent.gen_optional_sub_object_no_ex()
    assert (
        opt_edge_2 is None
    ), "We should not be able to load the optional edge with no example"
