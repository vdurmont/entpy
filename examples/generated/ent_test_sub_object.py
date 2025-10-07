from __future__ import annotations
from entpy import Ent, generate_uuid
from uuid import UUID
from datetime import datetime, UTC
from typing import Self
from evc import ExampleViewerContext
from database import get_session
from .ent_model import EntModel
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy import String
from ent_test_sub_object_schema import EntTestSubObjectSchema
from sqlalchemy import select, Select
from sqlalchemy.orm import Mapped, mapped_column
from typing import Any
from entpy import Field
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

    @classmethod
    def query(cls, vc: ExampleViewerContext) -> EntTestSubObjectQuery:
        return EntTestSubObjectQuery(vc=vc)


class EntTestSubObjectQuery:
    vc: ExampleViewerContext
    query: Select[tuple[EntTestSubObjectModel]]

    def __init__(self, vc: ExampleViewerContext) -> None:
        self.vc = vc
        self.query = select(EntTestSubObjectModel)

    def join(self, model_class: type[EntModel], predicate: ColumnElement[bool]) -> Self:
        self.query = self.query.join(model_class, predicate)
        return self

    def where(self, predicate: ColumnElement[bool]) -> Self:
        self.query = self.query.where(predicate)
        return self

    def order_by(self, predicate: ColumnElement[Any]) -> Self:
        self.query = self.query.order_by(predicate)
        return self

    def limit(self, limit: int) -> Self:
        self.query = self.query.limit(limit)
        return self

    async def gen(self) -> list[EntTestSubObject]:
        session = get_session()
        result = await session.execute(self.query)
        models = result.scalars().all()
        ents = [
            await EntTestSubObject._gen_from_model(self.vc, model) for model in models
        ]
        return list(filter(None, ents))

    async def gen_first(self) -> EntTestSubObject | None:
        session = get_session()
        result = await session.execute(self.query.limit(1))
        model = result.scalar_one_or_none()
        return await EntTestSubObject._gen_from_model(self.vc, model)


class EntTestSubObjectMutator:
    @classmethod
    def create(
        cls,
        vc: ExampleViewerContext,
        email: str,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> EntTestSubObjectMutatorCreationAction:
        return EntTestSubObjectMutatorCreationAction(
            vc=vc, id=id, created_at=created_at, email=email
        )

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

    def __init__(
        self,
        vc: ExampleViewerContext,
        id: UUID | None,
        created_at: datetime | None,
        email: str,
    ) -> None:
        self.vc = vc
        self.created_at = created_at if created_at else datetime.now(tz=UTC)
        self.id = id if id else generate_uuid(EntTestSubObject, self.created_at)
        self.email = email

    async def gen_savex(self) -> EntTestSubObject:
        session = get_session()
        model = EntTestSubObjectModel(
            id=self.id,
            created_at=self.created_at,
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
        cls,
        vc: ExampleViewerContext,
        created_at: datetime | None = None,
        email: str | Sentinel = NOTHING,
    ) -> EntTestSubObject:
        # TODO make sure we only use this in test mode

        email = "vdurmont@gmail.com" if isinstance(email, Sentinel) else email

        return await EntTestSubObjectMutator.create(
            vc=vc, created_at=created_at, email=email
        ).gen_savex()

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
