from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from entpy.model import APIEntity
from generated import ent_test_object3
from generated.all_models import ensure_api_models_built
from generated.ent_inherited_owner import EntInheritedOwnerDetailedAPIModel
from generated.ent_inherited_test import (
    EntInheritedTestDetailedAPIModel,
    EntInheritedTestItemAPIModel,
)
from generated.ent_inherited_test2 import EntInheritedTest2ItemAPIModel
from generated.ent_test_object import EntTestObjectItemAPIModel

from ent_test_thing_pattern import ThingStatus

IDENTITY = {"id", "entity_type", "created_at", "updated_at", "soft_deleted_at"}
AT = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


@pytest.fixture(autouse=True)
def built() -> None:
    ensure_api_models_built()


def identity(entity_type: str) -> dict[str, Any]:
    return {
        "id": uuid4(),
        "entity_type": entity_type,
        "created_at": AT,
        "updated_at": AT,
        "soft_deleted_at": None,
    }


def test_each_tier_carries_its_fields_and_the_lower_tiers() -> None:
    item = set(EntInheritedTestItemAPIModel.model_fields)
    detailed = set(EntInheritedTestDetailedAPIModel.model_fields)

    assert item == IDENTITY | {"base_field", "happened_at", "schema_field"}
    assert detailed == item | {"middle", "grand_parent"}


def test_inherited_pattern_fields_validate_and_dump() -> None:
    model = EntInheritedTestDetailedAPIModel.model_validate(
        {
            **identity("EntInheritedTest"),
            "base_field": "base",
            "happened_at": AT,
            "schema_field": "schema",
            "middle": 7,
            "grand_parent": None,
        }
    )

    result = model.model_dump(mode="json")

    assert result["happened_at"] == "2026-01-02T03:04:05+00:00"
    assert result["created_at"] == "2026-01-02T03:04:05+00:00"
    assert result["middle"] == 7
    assert "middle_field" not in result


def test_edge_to_a_pattern_dumps_the_concrete_model() -> None:
    target = EntInheritedTest2ItemAPIModel.model_validate(
        {
            **identity("EntInheritedTest2"),
            "base_field": "base",
            "happened_at": None,
            "schema_field": "concrete",
        }
    )
    owner = EntInheritedOwnerDetailedAPIModel.model_validate(
        {**identity("EntInheritedOwner"), "name": "owner", "inherited": target}
    )

    result = owner.model_dump(mode="json")

    assert result["inherited"]["entity_type"] == "EntInheritedTest2"
    assert result["inherited"]["schema_field"] == "concrete"


def test_enum_fields_dump_their_value() -> None:
    model = EntTestObjectItemAPIModel.model_validate(
        {**identity("EntTestObject"), "thing_status": ThingStatus.GOOD}
    )

    assert model.model_dump(mode="json")["thing_status"] == "GOOD"


def test_an_ent_exposing_no_field_gets_no_api_model() -> None:
    api_models = [
        obj
        for obj in vars(ent_test_object3).values()
        if isinstance(obj, type) and issubclass(obj, APIEntity)
    ]

    assert api_models == []
