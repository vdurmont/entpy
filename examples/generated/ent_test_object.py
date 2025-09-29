from __future__ import annotations

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from examples.database import generate_session
from framework.viewer_context import ViewerContext

from .ent_model import EntModel


class EntTestObjectModel(EntModel):
    __tablename__ = "test_object"

    firstname: Mapped[str] = mapped_column(String(100))


class EntTestObject:
    vc: ViewerContext
    model: EntTestObjectModel

    def __init__(self, vc: ViewerContext, model: EntTestObjectModel) -> None:
        self.vc = vc
        self.model = model

    @property
    def firstname(self) -> str:
        return self.model.firstname

    @classmethod
    async def gen(cls, vc: ViewerContext, ent_id: UUID) -> EntTestObject | None:
        async for session in generate_session():
            model = await session.get(EntTestObjectModel, ent_id)
            return await cls._gen_from_model(vc, model)

    @classmethod
    async def _gen_from_model(
        cls, vc: ViewerContext, model: EntTestObjectModel | None
    ) -> EntTestObject | None:
        if not model:
            return None
        ent = EntTestObject(vc=vc, model=model)
        # TODO check privacy here
        return ent
