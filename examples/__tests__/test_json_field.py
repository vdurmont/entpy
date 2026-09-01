import json
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from evc import ExampleViewerContext
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)
from sqlalchemy.exc import StatementError

# limited_json is declared as JsonField("limited_json", "list[str]", length=100).
LIMITED_JSON_LENGTH = 100


def _list_encoding_to(length: int) -> list[str]:
    """Build a list[str] whose JSON encoding is exactly `length` characters."""
    # '["' + padding + '"]' is 4 characters of overhead around the single item.
    value = ["A" * (length - 4)]
    assert len(json.dumps(value)) == length
    return value


@contextmanager
def _raises_too_long(encoded_length: int) -> Iterator[None]:
    """Assert the block rejects a JSON value of `encoded_length` characters.

    The limit is enforced in the column's bind processor, so the ValueError it
    raises reaches the caller wrapped in a SQLAlchemy StatementError.
    """
    with pytest.raises(StatementError) as excinfo:
        yield

    cause = excinfo.value.orig
    assert isinstance(cause, ValueError), f"expected a ValueError, got {cause!r}"
    assert str(cause) == (
        f"Encoded JSON is {encoded_length} characters, "
        f"which exceeds the maximum of {LIMITED_JSON_LENGTH}"
    )


async def test_json_field_at_limit(vc: ExampleViewerContext) -> None:
    """A JSON value encoding to exactly the limit is accepted."""
    value = _list_encoding_to(LIMITED_JSON_LENGTH)
    ent = await EntTestObjectExample.gen_create(vc, firstname="Bob", limited_json=value)

    reloaded = await EntTestObject.genx(vc, ent.id)
    assert reloaded.limited_json == value, (
        "a value encoding to exactly the limit should be stored"
    )


async def test_json_field_over_limit_on_create(vc: ExampleViewerContext) -> None:
    """Creating an ent with a JSON value over the limit fails."""
    value = _list_encoding_to(LIMITED_JSON_LENGTH + 1)
    with _raises_too_long(LIMITED_JSON_LENGTH + 1):
        await EntTestObjectExample.gen_create(vc, firstname="Carol", limited_json=value)


async def test_json_field_over_limit_on_update(vc: ExampleViewerContext) -> None:
    """Updating a JSON field to a value over the limit fails."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Dave")

    mut = EntTestObjectMutator.update(vc, ent)
    mut.limited_json = _list_encoding_to(LIMITED_JSON_LENGTH + 1)
    with _raises_too_long(LIMITED_JSON_LENGTH + 1):
        await mut.gen_savex()


async def test_json_field_without_limit_is_unbounded(vc: ExampleViewerContext) -> None:
    """A JsonField declared without a length accepts arbitrarily long values."""
    value = _list_encoding_to(10 * LIMITED_JSON_LENGTH)
    ent = await EntTestObjectExample.gen_create(vc, firstname="Frank", some_json=value)

    reloaded = await EntTestObject.genx(vc, ent.id)
    assert reloaded.some_json == value, "some_json should have no length limit"


async def test_json_field_limit_allows_none(vc: ExampleViewerContext) -> None:
    """A null JSON value is not subject to the length check."""
    ent = await EntTestObjectExample.gen_create(
        vc, firstname="Grace", limited_json=None
    )

    reloaded = await EntTestObject.genx(vc, ent.id)
    assert reloaded.limited_json is None, "limited_json should accept None"
