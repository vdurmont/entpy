from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID
from entpy import ViewerContext


class IEntTestThing(ABC):
    @property
    @abstractmethod
    def a_good_thing(self) -> str:
        pass

    @classmethod
    async def gen(cls, vc: ViewerContext, ent_id: UUID) -> IEntTestThing | None:
        # TODO refactor this to read the bytes from the UUID

        from .ent_test_object import EntTestObject

        ent_test_object = await EntTestObject.gen(vc, ent_id)
        if ent_test_object:
            return ent_test_object

        return None

    @classmethod
    async def genx(cls, vc: ViewerContext, ent_id: UUID) -> IEntTestThing:
        # TODO refactor this to read the bytes from the UUID

        from .ent_test_object import EntTestObject

        ent_test_object = await EntTestObject.genx(vc, ent_id)
        if ent_test_object:
            return ent_test_object

        raise ValueError(f"No EntTestThing found for ID {ent_id}")
