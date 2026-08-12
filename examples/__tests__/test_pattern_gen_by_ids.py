"""`gen_by_ids()` reads many ents of one pattern in a query per implementation.

The pattern under test is non-queryable and its two implementations live in
different database schemas, so there is no view to select from and no single
statement that could span them. Grouping by the type carried in each id is what
makes a bounded read possible at all.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID, uuid4

from database import engine
from entpy.framework.database import db
from evc import ExampleTestViewerContext, ExampleViewerContext
from sqlalchemy import event

from generated.ent_unqueryable import IEntUnqueryable
from generated.ent_unqueryable_child import (
    EntUnqueryableChild,
    EntUnqueryableChildExample,
    EntUnqueryableChildMutator,
)
from generated.ent_unqueryable_sibling import (
    EntUnqueryableSibling,
    EntUnqueryableSiblingExample,
)


@contextmanager
def count_selects() -> Iterator[list[str]]:
    statements: list[str] = []

    def _on_execute(statement: str, **_kwargs: object) -> None:
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", _on_execute, named=True)
    try:
        yield statements
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", _on_execute)


async def test_resolves_both_implementations_in_one_call(
    vc: ExampleViewerContext,
) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc, label="a child")
    sibling = await EntUnqueryableSiblingExample.gen_create(vc, label="a sibling")

    ents = await IEntUnqueryable.gen_by_ids(vc, [child.id, sibling.id])

    assert set(ents) == {child.id, sibling.id}
    assert isinstance(ents[child.id], EntUnqueryableChild)
    assert isinstance(ents[sibling.id], EntUnqueryableSibling)
    assert ents[child.id].label == "a child"
    assert ents[sibling.id].label == "a sibling"


async def test_cost_is_per_implementation_not_per_id(
    vc: ExampleViewerContext,
) -> None:
    few = [(await EntUnqueryableChildExample.gen_create(vc)).id for _ in range(2)]
    many = [(await EntUnqueryableChildExample.gen_create(vc)).id for _ in range(8)]

    forget_cached_queries()
    with count_selects() as for_few:
        assert len(await IEntUnqueryable.gen_by_ids(vc, few)) == 2

    forget_cached_queries()
    with count_selects() as for_many:
        assert len(await IEntUnqueryable.gen_by_ids(vc, many)) == 8

    assert len(for_many) == len(for_few), (
        f"{len(for_few)} selects for 2 ids but {len(for_many)} for 8: the read "
        "is not batched"
    )


async def test_one_query_per_distinct_type_present(
    vc: ExampleViewerContext,
) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc)
    sibling = await EntUnqueryableSiblingExample.gen_create(vc)

    forget_cached_queries()
    with count_selects() as one_type:
        await IEntUnqueryable.gen_by_ids(vc, [child.id])

    forget_cached_queries()
    with count_selects() as two_types:
        await IEntUnqueryable.gen_by_ids(vc, [child.id, sibling.id])

    assert len(two_types) == len(one_type) + 1


async def test_no_ids_reads_nothing(vc: ExampleViewerContext) -> None:
    with count_selects() as statements:
        assert await IEntUnqueryable.gen_by_ids(vc, []) == {}

    assert statements == []


async def test_a_missing_id_is_absent_rather_than_an_error(
    vc: ExampleViewerContext,
) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc)
    # Same ent type in the id, so it routes to a real table and finds no row.
    absent = _with_type_of(child.id)

    ents = await IEntUnqueryable.gen_by_ids(vc, [child.id, absent])

    assert set(ents) == {child.id}


async def test_soft_deleted_are_excluded(vc: ExampleViewerContext) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc)
    await EntUnqueryableChildMutator.soft_delete(vc, child).gen_save()

    assert await IEntUnqueryable.gen_by_ids(vc, [child.id]) == {}
    # Asking for them is not enough with a regular viewer: reading a
    # soft-deleted ent is a privacy decision, not a query filter.
    assert (
        await IEntUnqueryable.gen_by_ids(vc, [child.id], include_soft_deleted=True)
        == {}
    )


async def test_soft_deleted_reachable_by_a_privileged_viewer(
    vc: ExampleViewerContext,
) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc)
    await EntUnqueryableChildMutator.soft_delete(vc, child).gen_save()
    test_vc = ExampleTestViewerContext()

    assert await IEntUnqueryable.gen_by_ids(test_vc, [child.id]) == {}

    ents = await IEntUnqueryable.gen_by_ids(
        test_vc, [child.id], include_soft_deleted=True
    )
    assert set(ents) == {child.id}


async def test_accepts_ids_as_strings(vc: ExampleViewerContext) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc)

    ents = await IEntUnqueryable.gen_by_ids(vc, [str(child.id)])

    assert set(ents) == {child.id}


async def test_duplicate_ids_are_read_once(vc: ExampleViewerContext) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc)

    forget_cached_queries()
    with count_selects() as statements:
        ents = await IEntUnqueryable.gen_by_ids(vc, [child.id, child.id])

    assert set(ents) == {child.id}
    assert len(statements) == 1


def _with_type_of(ent_id: UUID) -> UUID:
    """A random id carrying the same ent type as `ent_id`."""
    random = uuid4().bytes
    return UUID(bytes=random[:6] + ent_id.bytes[6:8] + random[8:])


def forget_cached_queries() -> None:
    """Drop the per-session query cache without discarding the session.

    Counting statements only means something if the second call actually goes to
    the database; `EntQuery._gen_cached` would otherwise answer it from the
    first. Resetting the session instead would roll back the rows under test.
    """
    db.session.info.pop("query", None)
