from datetime import UTC, datetime

from entpy.model import TieredAPIEntity
from evc import ExampleTestViewerContext, ExampleViewerContext
from generated import ent_test_object3
from generated.ent_child import EntChild, EntChildExample, EntChildMutator
from generated.ent_grand_parent import EntGrandParentExample
from generated.ent_inherited_owner import EntInheritedOwnerExample
from generated.ent_inherited_test import EntInheritedTestExample
from generated.ent_inherited_test2 import EntInheritedTest2Example
from generated.ent_parent import EntParentExample
from tiers import Tier


async def test_ref_carries_only_identity(vc: ExampleViewerContext) -> None:
    child = await EntChildExample.gen_create(vc, name="Benjamin")

    result = (await child.gen_serialize(Tier.REF)).model_dump(mode="json")

    assert result == {
        "id": str(child.id),
        "entity_type": "EntChild",
        "created_at": child.created_at.isoformat(),
        "updated_at": child.updated_at.isoformat(),
        "soft_deleted_at": None,
    }


async def test_soft_deleted_ent_carries_its_deletion_time(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc)
    await EntChildMutator.soft_delete(vc, child).gen_save()
    deleted = await EntChild.genx(
        ExampleTestViewerContext(), child.id, include_soft_deleted=True
    )

    result = (await deleted.gen_serialize(Tier.REF)).model_dump(mode="json")

    assert deleted.soft_deleted_at is not None
    assert result["soft_deleted_at"] == deleted.soft_deleted_at.isoformat()


async def test_item_nests_edges_at_the_field_tier(vc: ExampleViewerContext) -> None:
    grand_parent = await EntGrandParentExample.gen_create(vc, name="Anne")
    parent = await EntParentExample.gen_create(
        vc, name="Vincent", grand_parent_id=grand_parent.id
    )
    child = await EntChildExample.gen_create(vc, name="Benjamin", parent_id=parent.id)

    result = (await child.gen_serialize(Tier.ITEM)).model_dump(mode="json")

    assert result["name"] == "Benjamin"
    assert result["parent"]["name"] == "Vincent"
    assert "grand_parent" not in result["parent"]
    assert "shout" not in result


async def test_detailed_includes_lower_tiers_and_computed_fields(
    vc: ExampleViewerContext,
) -> None:
    child = await EntChildExample.gen_create(vc, name="Benjamin")

    result = (await child.gen_serialize(Tier.DETAILED)).model_dump(mode="json")

    assert result["name"] == "Benjamin"
    assert result["shout"] == "BENJAMIN"
    assert result["parent"]["entity_type"] == "EntParent"


async def test_tier_default_nesting(vc: ExampleViewerContext) -> None:
    grand_parent = await EntGrandParentExample.gen_create(vc, name="Anne")
    parent = await EntParentExample.gen_create(vc, grand_parent_id=grand_parent.id)

    item = (await parent.gen_serialize(Tier.ITEM)).model_dump(mode="json")
    detailed = (await parent.gen_serialize(Tier.DETAILED)).model_dump(mode="json")

    assert "grand_parent" not in item
    assert detailed["grand_parent"]["name"] == "Anne"
    assert detailed["grand_parent"]["entity_type"] == "EntGrandParent"


async def test_pattern_fields_are_inherited_and_renamed(
    vc: ExampleViewerContext,
) -> None:
    grand_parent = await EntGrandParentExample.gen_create(vc, name="Anne")
    happened_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    ent = await EntInheritedTestExample.gen_create(
        vc,
        base_field="base",
        middle_field=7,
        schema_field="schema",
        happened_at=happened_at,
        grand_parent_id=grand_parent.id,
    )

    item = (await ent.gen_serialize(Tier.ITEM)).model_dump(mode="json")
    detailed = (await ent.gen_serialize(Tier.DETAILED)).model_dump(mode="json")

    assert item["base_field"] == "base"
    assert item["schema_field"] == "schema"
    assert "middle" not in item
    assert item["happened_at"] == "2026-01-02T03:04:05+00:00"
    assert detailed["middle"] == 7
    assert "middle_field" not in detailed
    assert detailed["grand_parent"]["name"] == "Anne"


async def test_edge_to_pattern_serializes_the_concrete_ent(
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


def test_an_ent_exposing_no_field_gets_no_api_model() -> None:
    api_models = [
        obj
        for obj in vars(ent_test_object3).values()
        if isinstance(obj, type) and issubclass(obj, TieredAPIEntity)
    ]

    assert api_models == []
