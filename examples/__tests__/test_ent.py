import uuid

import pytest
from entpy import EntNotFoundError, ValidationError
from ent_test_object_schema import Status
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)
from generated.ent_test_sub_object import EntTestSubObject  # noqa: F401
from evc import ExampleViewerContext


async def test_ent_test_object_gen_with_existing_model(
    vc: ExampleViewerContext,
) -> None:
    ent = await EntTestObjectExample.gen_create(vc, firstname="Vincent")

    result = await EntTestObject.gen(vc, ent.id)

    assert result is not None, "gen should not return None for a valid ID"
    assert result.firstname == "Vincent"


async def test_ent_test_object_gen_with_unknown_model(
    vc: ExampleViewerContext,
) -> None:
    ent_id = uuid.uuid4()
    result = await EntTestObject.gen(vc, ent_id)

    assert result is None, "gen should return None for an invalid ID"


async def test_ent_test_object_genx_with_existing_model(
    vc: ExampleViewerContext,
) -> None:
    ent = await EntTestObjectExample.gen_create(vc, firstname="Vincent")

    result = await EntTestObject.genx(vc, ent.id)

    assert result is not None, "genx should not return None for a valid ID"
    assert result.firstname == "Vincent"


async def test_ent_test_object_genx_with_unknown_model(
    vc: ExampleViewerContext,
) -> None:
    ent_id = uuid.uuid4()
    with pytest.raises(EntNotFoundError):
        await EntTestObject.genx(vc, ent_id)


async def test_edges_work_well(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc, firstname="Vincent")

    # Check required
    assert ent.required_sub_object_id is not None, (
        "We should be able to access the required edge's ID"
    )
    req_edge = await ent.gen_required_sub_object()
    assert req_edge is not None, "We should be able to load the required edge"

    # Check optional, but example generated
    assert ent.optional_sub_object_id is not None, "Example generates a sub object"
    opt_edge = await ent.gen_optional_sub_object()
    assert opt_edge is not None, "We should be able to load the optional edge"

    # Check optional, but example cancelled
    assert ent.optional_sub_object_no_ex_id is None, (
        "Example does not generate a sub object"
    )
    opt_edge_2 = await ent.gen_optional_sub_object_no_ex()
    assert opt_edge_2 is None, (
        "We should not be able to load the optional edge with no example"
    )


async def test_pattern_fields_are_written_properly(
    vc: ExampleViewerContext,
) -> None:
    good = "Taking a nap"
    ent = await EntTestObjectExample.gen_create(vc, a_good_thing=good)

    result = await EntTestObject.genx(vc, ent.id)

    assert result.a_good_thing == good


async def test_gen_and_genx_from_unique_field(vc: ExampleViewerContext) -> None:
    username = "vdurmont_" + str(uuid.uuid4())
    other_username = "vdurmont_" + str(uuid.uuid4())

    ent = await EntTestObjectExample.gen_create(vc, username=username)
    assert ent.username == username

    result = await EntTestObject.gen_from_username(vc, username)
    assert result is not None
    assert result.username == username

    result = await EntTestObject.gen_from_username(vc, other_username)
    assert result is None

    resultx = await EntTestObject.genx_from_username(vc, username)
    assert resultx.username == username

    with pytest.raises(EntNotFoundError):
        await EntTestObject.genx_from_username(vc, other_username)


async def test_enum_field(vc: ExampleViewerContext) -> None:
    status = Status.SAD
    ent = await EntTestObjectExample.gen_create(vc, status=status)
    assert ent.status == status


async def test_string_field_with_default(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc)
    assert ent.lastname == "Doe"


async def test_enum_field_with_default(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc)
    assert ent.sadness == Status.SAD


async def test_gen_with_string_id(vc: ExampleViewerContext) -> None:
    """Test that gen accepts a string UUID and converts it correctly."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Vincent")

    # Convert UUID to string and use it to fetch the entity
    result = await EntTestObject.gen(vc, str(ent.id))

    assert result is not None, "gen should accept string UUID"
    assert result.id == ent.id
    assert result.firstname == "Vincent"


async def test_genx_with_string_id(vc: ExampleViewerContext) -> None:
    """Test that genx accepts a string UUID and converts it correctly."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Vincent")

    # Convert UUID to string and use it to fetch the entity
    result = await EntTestObject.genx(vc, str(ent.id))

    assert result is not None, "genx should accept string UUID"
    assert result.id == ent.id
    assert result.firstname == "Vincent"


async def test_gen_with_invalid_string_id(vc: ExampleViewerContext) -> None:
    """Test that gen raises ValidationError for invalid UUID strings."""
    with pytest.raises(ValidationError, match="Invalid ID format"):
        await EntTestObject.gen(vc, "not-a-valid-uuid")


async def test_genx_with_invalid_string_id(vc: ExampleViewerContext) -> None:
    """Test that genx raises ValidationError for invalid UUID strings."""
    with pytest.raises(ValidationError, match="Invalid ID format"):
        await EntTestObject.genx(vc, "not-a-valid-uuid")
