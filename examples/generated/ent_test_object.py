from __future__ import annotations

from uuid import UUID, uuid4

from sentinels import NOTHING, Sentinel  # type: ignore
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from examples.database import get_session
from framework.viewer_context import ViewerContext

from .ent_model import EntModel


class EntTestObjectModel(EntModel):
    __tablename__ = "test_object"

    firstname: Mapped[str] = mapped_column(String(100), nullable=False)
    lastname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)


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
    def lastname(self) -> str | None:
        return self.model.lastname

    @property
    def city(self) -> str | None:
        return self.model.city

    @classmethod
    async def genx(cls, vc: ViewerContext, ent_id: UUID) -> EntTestObject:
        ent = await cls.gen(vc, ent_id)
        if not ent:
            raise ValueError("No {base_name} found for ID {ent_id}")
        return ent

    @classmethod
    async def gen(cls, vc: ViewerContext, ent_id: UUID) -> EntTestObject | None:
        session = get_session()
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

    @classmethod
    async def _genx_from_model(
        cls, vc: ViewerContext, model: EntTestObjectModel
    ) -> EntTestObject:
        ent = EntTestObject(vc=vc, model=model)
        # TODO check privacy here
        return ent


class EntTestObjectMutator:
    @classmethod
    def create(
        cls,
        vc: ViewerContext,
        firstname: str,
        lastname: str | None = None,
        city: str | None = None,
    ) -> EntTestObjectMutatorCreationAction:
        return EntTestObjectMutatorCreationAction(
            vc=vc, firstname=firstname, lastname=lastname, city=city
        )

    @classmethod
    def update(
        cls, vc: ViewerContext, ent: EntTestObject
    ) -> EntTestObjectMutatorUpdateAction:
        return EntTestObjectMutatorUpdateAction(vc=vc, ent=ent)


class EntTestObjectMutatorCreationAction:
    vc: ViewerContext
    id: UUID
    firstname: str
    city: str | None = None
    lastname: str | None = None

    def __init__(
        self, vc: ViewerContext, firstname: str, city: str | None, lastname: str | None
    ) -> None:
        self.vc = vc
        self.id = uuid4()
        self.firstname = firstname
        self.city = city
        self.lastname = lastname

    async def gen_savex(self) -> EntTestObject:
        session = get_session()
        model = EntTestObjectModel(
            id=self.id,
            firstname=self.firstname,
            city=self.city,
            lastname=self.lastname,
        )
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await EntTestObject._genx_from_model(self.vc, model)


class EntTestObjectMutatorUpdateAction:
    vc: ViewerContext
    ent: EntTestObject
    id: UUID
    firstname: str
    city: str | None = None
    lastname: str | None = None

    def __init__(self, vc: ViewerContext, ent: EntTestObject) -> None:
        self.vc = vc
        self.ent = ent
        self.firstname = ent.firstname
        self.city = ent.city
        self.lastname = ent.lastname

    async def gen_savex(self) -> EntTestObject:
        session = get_session()
        model = self.ent.model
        model.firstname = self.firstname
        model.city = self.city
        model.lastname = self.lastname
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await EntTestObject._genx_from_model(self.vc, model)


class EntTestObjectExample:
    @classmethod
    async def gen_create(
        cls,
        vc: ViewerContext,
        firstname: str | Sentinel = NOTHING,
        lastname: str | None = None,
        city: str | None = None,
    ) -> EntTestObject:
        # TODO make sure we only use this in test mode

        firstname = "Vincent" if isinstance(firstname, Sentinel) else firstname
        city = "Los Angeles" if isinstance(city, Sentinel) else city

        return await EntTestObjectMutator.create(
            vc=vc, firstname=firstname, lastname=lastname, city=city
        ).gen_savex()
