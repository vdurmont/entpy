import uuid

import pytest
from sqlalchemy.orm import Session

from examples.database import SessionLocal, init_db
from examples.generated.ent_test_object import EntTestObject, EntTestObjectModel
from framework.viewer_context import ViewerContext


@pytest.fixture
def db_session():
    """Fixture to provide a database session for tests"""
    init_db()
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def vc():
    """Fixture to provide a viewer context for tests"""
    return ViewerContext()


async def test_ent_test_object_gen_nullable_returns_none(
    db_session: Session, vc: ViewerContext
):
    ent_id = uuid.uuid4()
    model = EntTestObjectModel(id=ent_id, firstname="Vincent")
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)

    result = await EntTestObject.gen_nullable(vc, ent_id)

    assert result is not None, "gen_nullable should not return None for a valid ID"
    assert result.model.firstname == "Vincent"
