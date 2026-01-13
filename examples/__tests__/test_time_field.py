from datetime import time

from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)
from evc import ExampleViewerContext


async def test_time_field_with_static_example(
    vc: ExampleViewerContext,
) -> None:
    """Test that TimeField with static example stores and retrieves correctly."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Alice")

    assert ent.start_time is not None, "start_time should be set from example"
    assert isinstance(ent.start_time, time), "start_time should be a time object"
    assert ent.start_time == time(9, 30, 0), "start_time should match the example value"


async def test_time_field_with_dynamic_example(
    vc: ExampleViewerContext,
) -> None:
    """Test that TimeField with dynamic example stores and retrieves correctly."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Bob")

    assert ent.end_time is not None, "end_time should be set from dynamic example"
    assert isinstance(ent.end_time, time), "end_time should be a time object"
    assert ent.end_time == time(17, 30, 0), (
        "end_time should match the dynamic example value"
    )


async def test_time_field_with_custom_value(
    vc: ExampleViewerContext,
) -> None:
    """Test that TimeField can be set to a custom value."""
    custom_time = time(14, 45, 30)
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Charlie",
        start_time=custom_time,
    )

    assert ent.start_time == custom_time, "start_time should match the custom value"


async def test_time_field_with_none(
    vc: ExampleViewerContext,
) -> None:
    """Test that TimeField can be set to None (nullable)."""
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="David",
        start_time=None,
    )

    assert ent.start_time is None, "start_time should be None when explicitly set"


async def test_time_field_persists_after_reload(
    vc: ExampleViewerContext,
) -> None:
    """Test that TimeField values persist after reloading the entity."""
    custom_time = time(8, 15, 0)
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Eve",
        start_time=custom_time,
    )

    # Reload the entity
    reloaded = await EntTestObject.genx(vc, ent.id)

    assert reloaded.start_time == custom_time, (
        "start_time should persist after reloading"
    )


async def test_time_field_with_microseconds(
    vc: ExampleViewerContext,
) -> None:
    """Test that TimeField can handle microseconds."""
    precise_time = time(12, 30, 45, 123456)
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Frank",
        end_time=precise_time,
    )

    assert ent.end_time == precise_time, "end_time should preserve microseconds"


async def test_time_field_boundary_values(
    vc: ExampleViewerContext,
) -> None:
    """Test TimeField with boundary values (midnight and just before midnight)."""
    midnight = time(0, 0, 0)
    ent1 = await EntTestObjectExample.gen_create(
        vc,
        firstname="George",
        start_time=midnight,
    )
    assert ent1.start_time == midnight, "Should handle midnight correctly"

    almost_midnight = time(23, 59, 59, 999999)
    ent2 = await EntTestObjectExample.gen_create(
        vc,
        firstname="Hannah",
        end_time=almost_midnight,
    )
    assert ent2.end_time == almost_midnight, (
        "Should handle time just before midnight correctly"
    )
