from __future__ import annotations

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from examples.database import get_session
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

    @classmethod
    async def gen_nullable(
        cls, vc: ViewerContext, ent_id: UUID
    ) -> EntTestObject | None:
        session_gen = get_session()
        session = next(session_gen)
        try:
            model = session.get(EntTestObjectModel, ent_id)
            return await cls._gen_nullable_from_model(vc, model)
        finally:
            try:
                next(session_gen)
            except StopIteration:
                pass

    @classmethod
    async def _gen_nullable_from_model(
        cls, vc: ViewerContext, model: EntTestObjectModel | None
    ) -> EntTestObject | None:
        if not model:
            return None
        ent = EntTestObject(vc=vc, model=model)
        # TODO check privacy here
        return ent
