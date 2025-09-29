from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from examples.database import generate_session
from framework.viewer_context import ViewerContext

from .ent_model import EntModel


class EntTestObjectModel(EntModel):
    __tablename__ = "test_object"

    firstname: Mapped[str] = mapped_column(String(100), nullable=False)
    lastname: Mapped[str] = mapped_column(String(100), nullable=True)


class EntTestObject:
    vc: ViewerContext
    model: EntTestObjectModel

    def __init__(self, vc: ViewerContext, model: EntTestObjectModel) -> None:
        self.vc = vc
        self.model = model

    @property
    def id(self) -> UUID:
        return self.model.id

    @property
    def firstname(self) -> str:
        return self.model.firstname

    @property
    def lastname(self) -> str:
        return self.model.lastname

    @classmethod
    async def genx(cls, vc: ViewerContext, ent_id: UUID) -> EntTestObject:
        ent = await cls.gen(vc, ent_id)
        if not ent:
            raise ValueError("No {base_name} found for ID {ent_id}")
        return ent

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


class EntTestObjectMutator:
    @classmethod
    def create(
        cls, vc: ViewerContext, firstname: str, lastname: str | None = None
    ) -> EntTestObjectMutatorCreationAction:
        return EntTestObjectMutatorCreationAction(vc, firstname, lastname)


class EntTestObjectMutatorCreationAction:
    vc: ViewerContext
    id: UUID
    firstname: str
    lastname: str = None

    def __init__(self, vc: ViewerContext, firstname: str, lastname: str | None) -> None:
        self.vc = vc
        self.id = uuid4()
        self.firstname = firstname
        self.lastname = lastname

    async def gen_savex(self) -> EntTestObject:
        async for session in generate_session():
            model = EntTestObjectModel(
                id=self.id,
                firstname=self.firstname,
                lastname=self.lastname,
            )
            session.add(model)
            await session.commit()
            # TODO privacy checks
            return await EntTestObject._gen_from_model(self.vc, model)
