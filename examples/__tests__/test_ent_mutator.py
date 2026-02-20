import uuid

import pytest
from entpy import ValidationError
from werkzeug.exceptions import Forbidden
from evc import ExampleViewerContext, ExampleTestViewerContext
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)
from generated.ent_single_rule import EntSingleRuleMutator, EntSingleRuleExample
from generated.ent_test_object5 import EntTestObject5Example, EntTestObject5Mutator
from generated.ent_test_sub_object import EntTestSubObject  # noqa: F401


async def test_creation(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectMutator.create(
        vc=vc,
        a_good_thing="Eating cheese",
        username="vdurmont",
        firstname="Vincent",
        required_sub_object_id=uuid.uuid4(),
        obj5_id=(await EntTestObject5Example.gen_create(vc)).id,
    ).gen_savex()

    assert ent is not None, "create should create the ent"
    assert ent.firstname == "Vincent"

    ent = await EntTestObject.genx(vc, ent.id)

    assert ent is not None, "created ents should be loadable"
    assert ent.firstname == "Vincent"


async def test_creation_or_403(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectMutator.create(
        vc=vc,
        a_good_thing="Eating cheese",
        username="vdurmont",
        firstname="Vincent",
        required_sub_object_id=uuid.uuid4(),
        obj5_id=(await EntTestObject5Example.gen_create(vc)).id,
    ).gen_savex_or_403()

    assert ent is not None, "create should create the ent"
    assert ent.firstname == "Vincent"


async def test_creation_or_403_forbidden(vc: ExampleViewerContext) -> None:
    with pytest.raises(Forbidden):
        await EntSingleRuleMutator.create(vc, name="Test Entity 2").gen_savex_or_403()


async def test_update(vc: ExampleViewerContext) -> None:
    name = "Chris"

    ent = await EntTestObjectExample.gen_create(vc=vc)

    assert ent.firstname != name, "In the setup, we have a different name."

    mut = EntTestObjectMutator.update(vc, ent)
    mut.firstname = name
    ent = await mut.gen_savex()

    assert ent.firstname == name, "Name should have been updated"


async def test_update_or_403(vc: ExampleViewerContext) -> None:
    name = "Chris"

    ent = await EntTestObjectExample.gen_create(vc=vc)

    assert ent.firstname != name, "In the setup, we have a different name."

    mut = EntTestObjectMutator.update(vc, ent)
    mut.firstname = name
    ent = await mut.gen_savex_or_403()

    assert ent.firstname == name, "Name should have been updated"


async def test_update_or_403_forbidden(vc: ExampleViewerContext) -> None:
    ent = await EntSingleRuleExample.gen_create(vc=ExampleTestViewerContext())
    mut = EntSingleRuleMutator.update(vc, ent)
    with pytest.raises(Forbidden):
        await mut.gen_savex_or_403()


async def test_creation_with_assigned_id(vc: ExampleViewerContext) -> None:
    custom_uuid = uuid.uuid4()
    ent = await EntTestObjectMutator.create(
        vc=vc,
        id=custom_uuid,
        a_good_thing="Eating cheese",
        username="vdurmont2",
        firstname="Vincent",
        required_sub_object_id=uuid.uuid4(),
        obj5_id=(await EntTestObject5Example.gen_create(vc)).id,
    ).gen_savex()

    assert ent.id == custom_uuid, "Mutator.create should honor custom uuids"


async def test_create_validated_field(vc: ExampleViewerContext) -> None:
    with pytest.raises(ValidationError):
        await EntTestObjectExample.gen_create(vc=vc, validated_field="Yolo")


async def test_update_validated_field(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc=vc)

    mut = EntTestObjectMutator.update(vc, ent)
    mut.validated_field = "Yolo"
    with pytest.raises(ValidationError):
        await mut.gen_savex()

    mut.validated_field = "y_olo"
    ent = await mut.gen_savex()

    assert ent.validated_field == "y_olo"


async def test_update_validated_pattern_field(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc=vc)

    mut = EntTestObjectMutator.update(vc, ent)
    mut.a_pattern_validated_field = "Yolo"
    with pytest.raises(ValidationError):
        await mut.gen_savex()

    mut.a_pattern_validated_field = "yolo"
    ent = await mut.gen_savex()

    assert ent.a_pattern_validated_field == "yolo"


async def test_create_with_boolfield_with_default(vc: ExampleViewerContext) -> None:
    ent = await EntTestObject5Mutator.create(vc=vc, obj5_field="Yo!").gen_savex()
    assert ent is not None
    assert ent.is_it_true
