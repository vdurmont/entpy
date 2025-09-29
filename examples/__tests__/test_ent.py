import uuid

import pytest
from sqlalchemy.orm import Session

from examples.database import SessionLocal, init_db
from examples.generated.ent_test_object import EntTestObject, EntTestObjectModel
from framework.viewer_context import ViewerContext


@pytest.fixture
async def db_session():
    await init_db()
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


@pytest.fixture
def vc():
    return ViewerContext()


async def test_ent_test_object_gen_with_existing_model(
    db_session: Session, vc: ViewerContext
):
    ent_id = uuid.uuid4()
    model = EntTestObjectModel(id=ent_id, firstname="Vincent")
    db_session.add(model)
    await db_session.commit()

    result = await EntTestObject.gen(vc, ent_id)

    assert result is not None, "gen should not return None for a valid ID"
    assert result.firstname == "Vincent"


async def test_ent_test_object_gen_with_unknown_model(
    db_session: Session, vc: ViewerContext
):
    ent_id = uuid.uuid4()
    result = await EntTestObject.gen(vc, ent_id)

    assert result is None, "gen should return None for an invalid ID"
