import asyncio
from generated.ent_test_object2 import EntTestObject2Example
from ent_test_object2_schema import EntTestObject2Schema
from entpy.framework.database import db, event_subscription
from evc import ExampleViewerContext


class TestEvents:
    async def test_record(self, vc: ExampleViewerContext) -> None:
        db.session.info.clear()
        obj = await EntTestObject2Example.gen_create(vc, some_field="test", limit=42)
        assert db.session.info.get("events") == [
            ("test_object2", {"id": obj.id, "some_field": "test"}),
            ("test_pattern", {"id": obj.id, "limit": 42}),
        ]

    async def test_dispatch_in_process(self, vc: ExampleViewerContext) -> None:
        async with event_subscription(
            EntTestObject2Schema, "some_field", "something"
        ) as queue:
            obj = await EntTestObject2Example.gen_create(vc, some_field="something")
            expected = {"id": str(obj.id), "some_field": "something"}
            await db.session.commit()
            payload = await asyncio.wait_for(queue.get(), timeout=1)
            assert payload == expected
