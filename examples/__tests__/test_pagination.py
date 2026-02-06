from generated.ent_test_sub_object import EntTestSubObject  # noqa: F401
from evc import ExampleViewerContext
from generated.ent_model import EntModel
from collections.abc import Callable
from typing import Any, TypeVar, Coroutine
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectModel,
)
from entpy import Ent
from entpy.framework.query import EntQuery


ENTTYPE = TypeVar("ENTTYPE", bound=Ent)
ENTMODEL = TypeVar("ENTMODEL", bound=EntModel)


async def gen_connection(
    vc: ExampleViewerContext,
    query: EntQuery[ExampleViewerContext, ENTTYPE, ENTMODEL, ENTMODEL],
    serializer: Callable[[ENTTYPE], Coroutine[Any, Any, dict[str, Any]]],
    limit: int,
    offset: int,
) -> dict[str, Any]:
    items = await query.limit(limit).offset(offset).gen()
    serialized_items = [await serializer(item) for item in items]
    count = await query.gen_count_NO_PRIVACY()
    return {
        "items": serialized_items,
        "pagination": {
            "total": count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < count,
        },
    }


async def serializer(ent: EntTestObject) -> dict[str, Any]:
    return {
        "id": ent.id,
        "firstname": ent.firstname,
        "created_at": ent.created_at.isoformat(),
    }


async def test_connection(vc: ExampleViewerContext) -> None:
    firstname = "john"
    first = await EntTestObjectExample.gen_create(vc, firstname=firstname)
    second = await EntTestObjectExample.gen_create(vc, firstname=firstname)
    third = await EntTestObjectExample.gen_create(vc, firstname=firstname)
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc)
    await EntTestObjectExample.gen_create(vc)

    query = (
        EntTestObject.query(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .order_by(EntTestObjectModel.id.desc())
    )

    conn = await gen_connection(vc, query, serializer, limit=2, offset=0)

    assert conn["pagination"]["total"] == 3
    assert conn["pagination"]["limit"] == 2
    assert conn["pagination"]["offset"] == 0
    assert conn["pagination"]["has_more"] is True
    assert len(conn["items"]) == 2
    assert conn["items"][0]["id"] == third.id
    assert conn["items"][1]["id"] == second.id

    query = (
        EntTestObject.query(vc)
        .where(EntTestObjectModel.firstname == firstname)
        .order_by(EntTestObjectModel.id.desc())
    )

    conn = await gen_connection(vc, query, serializer, limit=3, offset=0)

    assert conn["pagination"]["total"] == 3
    assert conn["pagination"]["limit"] == 3
    assert conn["pagination"]["offset"] == 0
    assert conn["pagination"]["has_more"] is False
    assert len(conn["items"]) == 3
    assert conn["items"][0]["id"] == third.id
    assert conn["items"][1]["id"] == second.id
    assert conn["items"][2]["id"] == first.id
