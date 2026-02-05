from evc import ExampleViewerContext
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)


async def test_int_field_with_default_value(
    vc: ExampleViewerContext,
) -> None:
    """Test that IntField with default value uses the default when not provided."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Alice")

    assert ent.retry_count is not None, "retry_count should be set from default"
    assert isinstance(ent.retry_count, int), "retry_count should be an int"
    assert ent.retry_count == 0, "retry_count should match the default value"


async def test_int_field_default_can_be_overridden(
    vc: ExampleViewerContext,
) -> None:
    """Test that IntField default value can be overridden with a custom value."""
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Bob",
        retry_count=5,
    )

    assert ent.retry_count == 5, "retry_count should match the custom value"


async def test_int_field_default_can_be_set_to_none(
    vc: ExampleViewerContext,
) -> None:
    """Test that IntField default value can be overridden with None."""
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Charlie",
    )
    assert ent.retry_count == 0, "retry_count should match the default value"

    mut = EntTestObjectMutator.update(vc, ent)
    mut.retry_count = None
    ent = await mut.gen_savex()

    assert ent.retry_count is None, "retry_count should be None when explicitly set"


async def test_int_field_default_persists_after_reload(
    vc: ExampleViewerContext,
) -> None:
    """Test that IntField default value persists after reloading the entity."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="David")
    assert ent.retry_count == 0

    # Reload the entity
    reloaded = await EntTestObject.genx(vc, ent.id)

    assert reloaded.retry_count == 0, (
        "retry_count should persist with default value after reloading"
    )


async def test_int_field_custom_value_persists_after_reload(
    vc: ExampleViewerContext,
) -> None:
    """Test that IntField custom value persists after reloading the entity."""
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Eve",
        retry_count=3,
    )

    # Reload the entity
    reloaded = await EntTestObject.genx(vc, ent.id)

    assert reloaded.retry_count == 3, (
        "retry_count should persist with custom value after reloading"
    )


async def test_int_field_with_example(
    vc: ExampleViewerContext,
) -> None:
    """Test that IntField with example stores and retrieves correctly."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Frank")

    assert ent.status_code is not None, "status_code should be set from example"
    assert isinstance(ent.status_code, int), "status_code should be an int"
    assert ent.status_code == 404, "status_code should match the example value"


async def test_int_field_with_negative_value(
    vc: ExampleViewerContext,
) -> None:
    """Test that IntField can store negative values."""
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="George",
        retry_count=-1,
    )

    assert ent.retry_count == -1, "retry_count should handle negative values"


async def test_int_field_with_large_value(
    vc: ExampleViewerContext,
) -> None:
    """Test that IntField can store large values."""
    large_value = 999999999
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Hannah",
        retry_count=large_value,
    )

    assert ent.retry_count == large_value, "retry_count should handle large values"
