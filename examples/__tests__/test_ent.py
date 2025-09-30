import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from examples.database import get_session, init_db
from examples.generated.ent_test_object import (
    EntTestObject,
    EntTestObjectModel,
    EntTestObjectMutator,
)
from framework.viewer_context import ViewerContext


@pytest.fixture
async def db_session():
    await init_db()
    return get_session()


@pytest.fixture
def vc():
    return ViewerContext()


async def test_ent_test_object_gen_with_existing_model(
    db_session: AsyncSession, vc: ViewerContext
):
    ent = await EntTestObjectMutator.create(
        vc=vc, firstname="Vincent", lastname="Durmont"
    ).gen_savex()

    result = await EntTestObject.gen(vc, ent.id)

    assert result is not None, "gen should not return None for a valid ID"
    assert result.firstname == "Vincent"


async def test_ent_test_object_gen_with_unknown_model(
    db_session: AsyncSession, vc: ViewerContext
):
    ent_id = uuid.uuid4()
    result = await EntTestObject.gen(vc, ent_id)

    assert result is None, "gen should return None for an invalid ID"


async def test_ent_test_object_genx_with_existing_model(
    db_session: AsyncSession, vc: ViewerContext
):
    ent_id = uuid.uuid4()
    model = EntTestObjectModel(id=ent_id, firstname="Vincent")
    db_session.add(model)
    await db_session.commit()

    result = await EntTestObject.genx(vc, ent_id)

    assert result is not None, "genx should not return None for a valid ID"
    assert result.firstname == "Vincent"


async def test_ent_test_object_genx_with_unknown_model(
    db_session: AsyncSession, vc: ViewerContext
):
    ent_id = uuid.uuid4()
    with pytest.raises(ValueError):
        await EntTestObject.genx(vc, ent_id)
