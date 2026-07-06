from evc import ExampleViewerContext
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)

# 2**31 - 1 == 2147483647 is the largest value a 32-bit signed integer can hold.
INT32_MAX = 2**31 - 1


async def test_big_int_field_with_example(
    vc: ExampleViewerContext,
) -> None:
    """Test that BigIntField with example stores and retrieves correctly."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Alice")

    assert ent.big_number is not None, "big_number should be set from example"
    assert isinstance(ent.big_number, int), "big_number should be an int"
    assert ent.big_number == 9_000_000_000, "big_number should match the example value"


async def test_big_int_field_stores_value_beyond_int32(
    vc: ExampleViewerContext,
) -> None:
    """Test that BigIntField can store values larger than a 32-bit integer."""
    big_value = INT32_MAX + 1
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Bob",
        big_number=big_value,
    )

    assert ent.big_number == big_value, "big_number should handle values > 2**31"


async def test_big_int_field_persists_after_reload(
    vc: ExampleViewerContext,
) -> None:
    """Test that a large BigIntField value persists after reloading the entity."""
    big_value = 2**62
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Charlie",
        big_number=big_value,
    )

    reloaded = await EntTestObject.genx(vc, ent.id)

    assert reloaded.big_number == big_value, (
        "big_number should persist with a large value after reloading"
    )


async def test_big_int_field_can_be_updated(
    vc: ExampleViewerContext,
) -> None:
    """Test that a BigIntField can be updated to another large value."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Dave")

    mut = EntTestObjectMutator.update(vc, ent)
    mut.big_number = 5_000_000_000
    ent = await mut.gen_savex()

    assert ent.big_number == 5_000_000_000, "big_number should reflect the update"


async def test_big_int_field_with_negative_value(
    vc: ExampleViewerContext,
) -> None:
    """Test that BigIntField can store large negative values."""
    big_value = -(2**40)
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Eve",
        big_number=big_value,
    )

    assert ent.big_number == big_value, "big_number should handle large negative values"
