import pytest
from werkzeug.exceptions import NotFound
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from unittest.mock import patch

from entpy import EntNotFoundError, db
from evc import ExampleTestViewerContext, ExampleViewerContext
from generated.ent_child import EntChild, EntChildExample, EntChildModel
from generated.ent_grand_parent import EntGrandParentExample
from generated.ent_parent import EntParentExample, EntParentModel
from generated.ent_single_rule import EntSingleRule, EntSingleRuleExample
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectModel,
)
from generated.ent_test_sub_object import EntTestSubObject  # noqa: F401


async def test_ent_query(vc: ExampleViewerContext) -> None:
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


async def test_ent_query_join(vc: ExampleViewerContext) -> None:
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


async def test_ent_query_count(vc: ExampleViewerContext) -> None:
    firstname = "john"
    await EntTestObjectExample.gen_create(vc, firstname=firstname)
    await EntTestObjectExample.gen_create(vc, firstname=firstname)
    await EntTestObjectExample.gen_create(vc, firstname=firstname)
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc)

    results = (
        await EntTestObject.query(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .gen_count()
    )

    assert results == 3


async def test_ent_query_count_force_no_privacy() -> None:
    # Create a TestViewerContext to create entities (they have privacy rules)
    test_vc = ExampleTestViewerContext()

    # Create 5 EntSingleRule entities (which have AllowIfTestViewerContext privacy rule)
    await EntSingleRuleExample.gen_create(test_vc, name="Entity 1")
    await EntSingleRuleExample.gen_create(test_vc, name="Entity 2")
    await EntSingleRuleExample.gen_create(test_vc, name="Entity 3")
    await EntSingleRuleExample.gen_create(test_vc, name="Entity 4")
    await EntSingleRuleExample.gen_create(test_vc, name="Entity 5")

    # Query with regular ExampleViewerContext (not TestViewerContext)
    # This means privacy rules will deny access
    regular_vc = ExampleViewerContext()

    # Without force_no_privacy, count should be 0 because privacy filters them out
    # (count is <= 50, so it loads entities and applies privacy)
    count_with_privacy = await EntSingleRule.query(regular_vc).gen_count()
    assert count_with_privacy == 0

    # With force_no_privacy=True, count should be 5 (bypasses privacy completely)
    count_without_privacy = await EntSingleRule.query(regular_vc).gen_count_NO_PRIVACY()
    assert count_without_privacy == 5


async def test_gen_first(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc)
    result = await EntTestObject.query(vc).gen_first()
    assert result is not None
    assert result.id == ent.id


async def test_genx_first(vc: ExampleViewerContext) -> None:
    with pytest.raises(EntNotFoundError):
        await EntTestObject.query(vc).genx_first()


async def test_genx_first_or_404(vc: ExampleViewerContext) -> None:
    with pytest.raises(NotFound):
        await EntTestObject.query(vc).genx_first_or_404()


async def test_cache_hit(vc: ExampleViewerContext) -> None:
    firstname = "jane"
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc, firstname=firstname)

    assert not db.session.info.get("query")
    results = (
        await EntTestObject.query(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .gen()
    )
    assert len(results) == 1
    assert db.session.info["query"]

    with patch("entpy.framework.query.db.session.scalars") as mock:
        results = (
            await EntTestObject.query(vc)
            .where(EntTestObjectModel.firstname == firstname)
            .gen()
        )
        mock.assert_not_called()
        assert len(results) == 1


async def test_cache_for_update(vc: ExampleViewerContext) -> None:
    firstname = "jane"
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc, firstname=firstname)

    assert not db.session.info.get("query")
    results = (
        await EntTestObject.query(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .gen()
    )
    assert len(results) == 1
    assert db.session.info["query"]

    with patch(
        "entpy.framework.query.db.session.scalars", side_effect=db.session.scalars
    ) as mock:
        results = (
            await EntTestObject.query(vc)
            .where(EntTestObjectModel.firstname == firstname)
            .gen(for_update=True)
        )
        mock.assert_called_once()
        assert len(results) == 1


async def test_cache_mutate(vc: ExampleViewerContext) -> None:
    firstname = "jane"
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc, firstname=firstname)

    assert not db.session.info.get("query")
    results = (
        await EntTestObject.query(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .gen()
    )
    assert len(results) == 1
    assert db.session.info["query"]

    await EntTestObjectExample.gen_create(vc, firstname=firstname)
    assert not db.session.info.get("query")

    results = (
        await EntTestObject.query(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .gen()
    )
    assert len(results) == 2
