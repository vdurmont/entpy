from __future__ import annotations
from entpy import Ent
from uuid import UUID, uuid4
from datetime import datetime
from evc import ExampleViewerContext
from database import get_session
from sqlalchemy.orm import Mapped, mapped_column
from ent_test_sub_object_schema import EntTestSubObjectSchema
from entpy import Field
from .ent_model import EntModel
from sqlalchemy import String
from sentinels import NOTHING, Sentinel  # type: ignore


class EntTestSubObjectModel(EntModel):
    __tablename__ = "test_sub_object"

    email: Mapped[str] = mapped_column(String(100), nullable=False)


class EntTestSubObject(Ent):
    vc: ExampleViewerContext
    model: EntTestSubObjectModel

    def __init__(self, vc: ExampleViewerContext, model: EntTestSubObjectModel) -> None:
        self.vc = vc
        self.model = model

    @property
    def id(self) -> UUID:
        return self.model.id

    @property
    def created_at(self) -> datetime:
        return self.model.created_at

    @property
    def updated_at(self) -> datetime:
        return self.model.updated_at

    @property
    def email(self) -> str:
        return self.model.email

    @classmethod
    async def genx(cls, vc: ExampleViewerContext, ent_id: UUID) -> EntTestSubObject:
        ent = await cls.gen(vc, ent_id)
        if not ent:
            raise ValueError(f"No EntTestSubObject found for ID {ent_id}")
        return ent

    @classmethod
    async def gen(
        cls, vc: ExampleViewerContext, ent_id: UUID
    ) -> EntTestSubObject | None:
        session = get_session()
        model = await session.get(EntTestSubObjectModel, ent_id)
        return await cls._gen_from_model(vc, model)

    @classmethod
    async def _gen_from_model(
        cls, vc: ExampleViewerContext, model: EntTestSubObjectModel | None
    ) -> EntTestSubObject | None:
        if not model:
            return None
        ent = EntTestSubObject(vc=vc, model=model)
        # TODO check privacy here
        return ent

    @classmethod
    async def _genx_from_model(
        cls, vc: ExampleViewerContext, model: EntTestSubObjectModel
    ) -> EntTestSubObject:
        ent = EntTestSubObject(vc=vc, model=model)
        # TODO check privacy here
        return ent


class EntTestSubObjectMutator:
    @classmethod
    def create(
        cls, vc: ExampleViewerContext, email: str
    ) -> EntTestSubObjectMutatorCreationAction:
        return EntTestSubObjectMutatorCreationAction(vc=vc, email=email)

    @classmethod
    def update(
        cls, vc: ExampleViewerContext, ent: EntTestSubObject
    ) -> EntTestSubObjectMutatorUpdateAction:
        return EntTestSubObjectMutatorUpdateAction(vc=vc, ent=ent)

    @classmethod
    def delete(
        cls, vc: ExampleViewerContext, ent: EntTestSubObject
    ) -> EntTestSubObjectMutatorDeletionAction:
        return EntTestSubObjectMutatorDeletionAction(vc=vc, ent=ent)


class EntTestSubObjectMutatorCreationAction:
    vc: ExampleViewerContext
    id: UUID
    email: str

    def __init__(self, vc: ExampleViewerContext, email: str) -> None:
        self.vc = vc
        self.id = uuid4()
        self.email = email

    async def gen_savex(self) -> EntTestSubObject:
        session = get_session()
        model = EntTestSubObjectModel(
            id=self.id,
            email=self.email,
        )
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await EntTestSubObject._genx_from_model(self.vc, model)


class EntTestSubObjectMutatorUpdateAction:
    vc: ExampleViewerContext
    ent: EntTestSubObject
    id: UUID
    email: str

    def __init__(self, vc: ExampleViewerContext, ent: EntTestSubObject) -> None:
        self.vc = vc
        self.ent = ent
        self.email = ent.email

    async def gen_savex(self) -> EntTestSubObject:
        session = get_session()
        model = self.ent.model
        model.email = self.email
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await EntTestSubObject._genx_from_model(self.vc, model)


class EntTestSubObjectMutatorDeletionAction:
    vc: ExampleViewerContext
    ent: EntTestSubObject

    def __init__(self, vc: ExampleViewerContext, ent: EntTestSubObject) -> None:
        self.vc = vc
        self.ent = ent

    async def gen_save(self) -> None:
        session = get_session()
        model = self.ent.model
        # TODO privacy checks
        await session.delete(model)
        await session.flush()


class EntTestSubObjectExample:
    @classmethod
    async def gen_create(
        cls, vc: ExampleViewerContext, email: str | Sentinel = NOTHING
    ) -> EntTestSubObject:
        # TODO make sure we only use this in test mode

        email = "vdurmont@gmail.com" if isinstance(email, Sentinel) else email

        return await EntTestSubObjectMutator.create(vc=vc, email=email).gen_savex()

    @classmethod
    def _get_field(cls, field_name: str) -> Field:
        schema = EntTestSubObjectSchema()
        fields = schema.get_fields()
        field = list(
            filter(
                lambda field: field.name == field_name,
                fields,
            )
        )[0]
        if not field:
            raise ValueError(f"Unknown field: {field_name}")
        return field
