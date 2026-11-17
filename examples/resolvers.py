from datetime import UTC, datetime

from computed_models import ChildComputedDetailed, ChildComputedItem, TopComputedItem
from generated.ent_child import EntChild
from generated.ent_inherited_test_top import IEntInheritedTestTop
from tiers import Tier


async def gen_child_computed_api_fields(
    children: list[EntChild], tier: Tier
) -> list[ChildComputedItem]:
    if tier == Tier.ITEM:
        return [ChildComputedItem(shout=child.name.upper()) for child in children]
    return [
        ChildComputedDetailed(shout=child.name.upper(), name_length=len(child.name))
        for child in children
    ]


async def gen_top_computed_api_fields(
    ents: list[IEntInheritedTestTop], tier: Tier
) -> list[TopComputedItem]:
    return [
        TopComputedItem(label=f"{ent.base_field}!", computed_at=datetime.now(UTC))
        for ent in ents
    ]
