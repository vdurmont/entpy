from datetime import UTC, datetime

import pytest
from entpy.model import APIEntity, get_computed_api_field_values
from evc import ExampleTestViewerContext, ExampleViewerContext
from generated import ent_test_object3
from generated.ent_child import EntChild, EntChildExample, EntChildMutator
from generated.ent_grand_parent import EntGrandParentExample
from generated.ent_inherited_owner import EntInheritedOwnerExample
from generated.ent_inherited_test import EntInheritedTestExample
from generated.ent_inherited_test2 import EntInheritedTest2Example
from generated.ent_inherited_test_middle import IEntInheritedTestMiddle
from generated.ent_parent import EntParentExample
from generated.ent_test_object import EntTestObjectExample
from tiers import Tier

from computed_models import ChildComputedDetailed, ChildComputedItem
from ent_test_thing_pattern import ThingStatus


async def test_item_carries_the_identity_and_item_fields(
    vc: ExampleViewerContext,
) -> None:
    grand_parent = await EntGrandParentExample.gen_create(vc, name="Anne")

    result = (await grand_parent.gen_serialize(Tier.ITEM)).model_dump(mode="json")

    assert result == {
        "id": str(grand_parent.id),
        "entity_type": "EntGrandParent",
        "created_at": grand_parent.created_at.isoformat(),
        "updated_at": grand_parent.updated_at.isoformat(),
        "soft_deleted_at": None,
        "name": "Anne",
    }


async def test_soft_deleted_ent_carries_its_deletion_time(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc)
    await EntChildMutator.soft_delete(vc, child).gen_save()
    deleted = await EntChild.genx(
        ExampleTestViewerContext(), child.id, include_soft_deleted=True
    )

    result = (await deleted.gen_serialize(Tier.ITEM)).model_dump(mode="json")

    assert deleted.soft_deleted_at is not None
    assert result["soft_deleted_at"] == deleted.soft_deleted_at.isoformat()


async def test_edges_nest_at_their_tier(vc: ExampleViewerContext) -> None:
    grand_parent = await EntGrandParentExample.gen_create(vc, name="Anne")
    parent = await EntParentExample.gen_create(
        vc, name="Vincent", grand_parent_id=grand_parent.id
    )
    child = await EntChildExample.gen_create(vc, name="Benjamin", parent_id=parent.id)

    child_item = (await child.gen_serialize(Tier.ITEM)).model_dump(mode="json")
    parent_detailed = (await parent.gen_serialize(Tier.DETAILED)).model_dump(
        mode="json"
    )

    assert child_item["parent"]["name"] == "Vincent"
    assert "grand_parent" not in child_item["parent"]
    assert parent_detailed["grand_parent"]["name"] == "Anne"
    assert parent_detailed["grand_parent"]["entity_type"] == "EntGrandParent"


async def test_detailed_adds_its_fields_to_item(vc: ExampleViewerContext) -> None:
    parent = await EntParentExample.gen_create(vc, name="Vincent")

    item = (await parent.gen_serialize(Tier.ITEM)).model_dump(mode="json")
    detailed = (await parent.gen_serialize(Tier.DETAILED)).model_dump(mode="json")

    assert "grand_parent" not in item
    assert detailed == {**item, "grand_parent": detailed["grand_parent"]}


async def test_pattern_fields_are_inherited_and_renamed(
    vc: ExampleViewerContext,
) -> None:
    grand_parent = await EntGrandParentExample.gen_create(vc, name="Anne")
    ent = await EntInheritedTestExample.gen_create(
        vc,
        base_field="base",
        middle_field=7,
        schema_field="schema",
        happened_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        grand_parent_id=grand_parent.id,
    )

    item = (await ent.gen_serialize(Tier.ITEM)).model_dump(mode="json")
    detailed = (await ent.gen_serialize(Tier.DETAILED)).model_dump(mode="json")

    assert item["base_field"] == "base"
    assert item["schema_field"] == "schema"
    assert item["happened_at"] == "2026-01-02T03:04:05+00:00"
    assert "middle" not in item
    assert detailed["middle"] == 7
    assert "middle_field" not in detailed
    assert detailed["grand_parent"]["name"] == "Anne"


async def test_a_missing_nullable_edge_is_null(vc: ExampleViewerContext) -> None:
    ent = await EntInheritedTestExample.gen_create(vc)

    result = (await ent.gen_serialize(Tier.DETAILED)).model_dump(mode="json")

    assert result["grand_parent"] is None


async def test_edge_to_a_pattern_serializes_the_concrete_ent(
    vc: ExampleViewerContext,
) -> None:
    target = await EntInheritedTest2Example.gen_create(
        vc, base_field="base", schema_field="concrete"
    )
    owner = await EntInheritedOwnerExample.gen_create(vc, inherited_id=target.id)

    result = (await owner.gen_serialize(Tier.DETAILED)).model_dump(mode="json")

    assert result["inherited"]["entity_type"] == "EntInheritedTest2"
    assert result["inherited"]["base_field"] == "base"
    assert result["inherited"]["schema_field"] == "concrete"


async def test_a_pattern_serializes_as_its_implementation(
    vc: ExampleViewerContext,
) -> None:
    created = await EntInheritedTest2Example.gen_create(vc, schema_field="concrete")
    ent = await IEntInheritedTestMiddle.genx(vc, created.id)

    result = (await ent.gen_serialize(Tier.ITEM)).model_dump(mode="json")

    assert result["entity_type"] == "EntInheritedTest2"
    assert result["schema_field"] == "concrete"


async def test_enum_fields_dump_their_value(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc, thing_status=ThingStatus.GOOD)

    result = (await ent.gen_serialize(Tier.ITEM)).model_dump(mode="json")

    assert result["thing_status"] == "GOOD"


def test_an_ent_exposing_no_field_gets_no_api_model() -> None:
    api_models = [
        obj
        for obj in vars(ent_test_object3).values()
        if isinstance(obj, type) and issubclass(obj, APIEntity)
    ]

    assert api_models == []


async def test_computed_fields_join_their_tier(vc: ExampleViewerContext) -> None:
    child = await EntChildExample.gen_create(vc, name="Benjamin")

    item = (await child.gen_serialize(Tier.ITEM)).model_dump(mode="json")
    detailed = (await child.gen_serialize(Tier.DETAILED)).model_dump(mode="json")

    assert item["shout"] == "BENJAMIN"
    assert "name_length" not in item
    assert detailed["shout"] == "BENJAMIN"
    assert detailed["name_length"] == 8


async def test_a_patterns_computed_fields_reach_every_implementation(
    vc: ExampleViewerContext,
) -> None:
    first = await EntInheritedTestExample.gen_create(vc, base_field="one")
    second = await EntInheritedTest2Example.gen_create(vc, base_field="two")

    first_item = (await first.gen_serialize(Tier.ITEM)).model_dump(mode="json")
    second_item = (await second.gen_serialize(Tier.ITEM)).model_dump(mode="json")

    assert first_item["label"] == "one!"
    assert second_item["label"] == "two!"
    assert first_item["computed_at"].endswith("+00:00")


def test_computed_values_must_match_the_tier_model() -> None:
    with pytest.raises(TypeError, match="expected ChildComputedDetailed"):
        get_computed_api_field_values(
            [ChildComputedItem(shout="A")], ChildComputedDetailed, 1
        )


def test_computed_values_must_cover_every_ent() -> None:
    with pytest.raises(ValueError, match="returned 0 results for 1 Ents"):
        get_computed_api_field_values([], ChildComputedItem, 1)
