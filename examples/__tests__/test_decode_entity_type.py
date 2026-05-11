import uuid

from evc import ExampleViewerContext
from generated.all_models import decode_entity_type_from_id
from generated.ent_test_object import EntTestObject, EntTestObjectExample
from generated.ent_user import EntUser, EntUserExample


async def test_decode_entity_type_from_ent_test_object(
    vc: ExampleViewerContext,
) -> None:
    ent = await EntTestObjectExample.gen_create(vc)

    result = decode_entity_type_from_id(ent.id)

    assert result is EntTestObject


async def test_decode_entity_type_from_ent_user(
    vc: ExampleViewerContext,
) -> None:
    ent = await EntUserExample.gen_create(vc)

    result = decode_entity_type_from_id(ent.id)

    assert result is EntUser


async def test_decode_entity_type_from_unknown_id() -> None:
    result = decode_entity_type_from_id(uuid.uuid4())

    assert result is None
