from uuid import uuid4
from datetime import datetime, UTC, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectModel,
)
from generated.ent_test_sub_object import EntTestSubObject  # noqa: F401
from evc import ExampleViewerContext


async def test_ent_query(db_session: AsyncSession, vc: ExampleViewerContext) -> None:
    firstname = str(uuid4())
    now = datetime.now(tz=UTC)

    # Message 1: prompt from user
    time = now - timedelta(minutes=100)
    _yes = await EntTestObjectExample.gen_create(
        vc, firstname=firstname, created_at=time
    )
    time = now - timedelta(minutes=90)
    yes2 = await EntTestObjectExample.gen_create(
        vc, firstname=firstname, created_at=time
    )
    time = now - timedelta(minutes=80)
    yes3 = await EntTestObjectExample.gen_create(
        vc, firstname=firstname, created_at=time
    )
    time = now - timedelta(minutes=70)
    _nope = await EntTestObjectExample.gen_create(
        vc, firstname=str(uuid4()), created_at=time
    )

    results = (
        await EntTestObject.query(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .order_by(EntTestObjectModel.created_at.desc())
        .limit(2)
        .gen()
    )

    assert len(results) == 2
    assert results[0].id == yes3.id
    assert results[1].id == yes2.id
