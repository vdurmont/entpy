import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from examples.generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)
from framework.viewer_context import ViewerContext


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
