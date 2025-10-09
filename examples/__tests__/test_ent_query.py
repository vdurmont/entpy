from uuid import uuid4
from datetime import datetime, UTC, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from generated.ent_grand_parent import EntGrandParentExample
from generated.ent_parent import EntParentExample, EntParentModel
from generated.ent_child import EntChildExample, EntChild, EntChildModel
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


async def test_ent_query_join(
    db_session: AsyncSession, vc: ExampleViewerContext
) -> None:
    now = datetime.now(tz=UTC)

    grand_parent1 = await EntGrandParentExample.gen_create(vc, name="Anne")
    grand_parent2 = await EntGrandParentExample.gen_create(vc, name="Michael")
    parent1 = await EntParentExample.gen_create(
        vc, name="Vincent", grand_parent_id=grand_parent1.id
    )
    parent2 = await EntParentExample.gen_create(
        vc, name="Rachel", grand_parent_id=grand_parent2.id
    )
    time = now - timedelta(minutes=100)
    child1 = await EntChildExample.gen_create(
        vc, name="Benjamin", created_at=time, parent_id=parent1.id
    )
    time = now - timedelta(minutes=90)
    child2 = await EntChildExample.gen_create(
        vc, name="Laura", created_at=time, parent_id=parent1.id
    )
    time = now - timedelta(minutes=80)
    _child3 = await EntChildExample.gen_create(
        vc, name="Quinn", created_at=time, parent_id=parent2.id
    )
    time = now - timedelta(minutes=70)
    _child4 = await EntChildExample.gen_create(
        vc, name="Harper", created_at=time, parent_id=parent2.id
    )

    results = (
        await EntChild.query(vc)
        .join(EntParentModel, EntChildModel.parent_id == EntParentModel.id)
        .where(EntParentModel.grand_parent_id == grand_parent1.id)
        .order_by(EntChildModel.created_at.desc())
        .gen()
    )

    assert len(results) == 2
    assert results[0].id == child2.id
    assert results[1].id == child1.id


async def test_ent_query_count(
    db_session: AsyncSession, vc: ExampleViewerContext
) -> None:
    firstname = "john"
    await EntTestObjectExample.gen_create(vc, firstname=firstname)
    await EntTestObjectExample.gen_create(vc, firstname=firstname)
    await EntTestObjectExample.gen_create(vc, firstname=firstname)
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc)

    results = (
        await EntTestObject.query_count(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .gen()
    )

    assert results == 3
