from __future__ import annotations
from entpy import Ent, generate_uuid
from uuid import UUID
from datetime import datetime, UTC
from typing import Self
from evc import ExampleViewerContext
from database import get_session
from .ent_test_sub_object import EntTestSubObject
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from entpy import Field, FieldWithDynamicExample
from sqlalchemy import Text
from .ent_model import EntModel
from sqlalchemy.dialects.postgresql import UUID as DBUUID
from typing import Any
from .ent_test_sub_object import EntTestSubObjectExample
from ent_test_object_schema import Status
from sqlalchemy import Enum as DBEnum
from sentinels import NOTHING, Sentinel  # type: ignore
from .ent_test_thing import IEntTestThing
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy import String
from ent_test_object_schema import EntTestObjectSchema
from sqlalchemy import select, Select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer


class EntTestObjectModel(EntModel):
    __tablename__ = "test_object"

    a_good_thing: Mapped[str] = mapped_column(String(100), nullable=False)
    firstname: Mapped[str] = mapped_column(String(100), nullable=False)
    required_sub_object_id: Mapped[UUID] = mapped_column(
        DBUUID(as_uuid=True), ForeignKey("test_sub_object.id"), nullable=False
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    context: Mapped[str | None] = mapped_column(Text(), nullable=True)
    lastname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    optional_sub_object_id: Mapped[UUID | None] = mapped_column(
        DBUUID(as_uuid=True), ForeignKey("test_sub_object.id"), nullable=True
    )
    optional_sub_object_no_ex_id: Mapped[UUID | None] = mapped_column(
        DBUUID(as_uuid=True), ForeignKey("test_sub_object.id"), nullable=True
    )
    self_id: Mapped[UUID | None] = mapped_column(
        DBUUID(as_uuid=True), ForeignKey("test_object.id"), nullable=True
    )
    status: Mapped[Status | None] = mapped_column(
        DBEnum(Status, native_enum=True), nullable=True
    )
    status_code: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    when_is_it_cool: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class EntTestObject(Ent, IEntTestThing):
    """
    This is an object we use to test all the ent framework features!
    """

    vc: ExampleViewerContext
    model: EntTestObjectModel

    def __init__(self, vc: ExampleViewerContext, model: EntTestObjectModel) -> None:
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
    def a_good_thing(self) -> str:
        return self.model.a_good_thing

    @property
    def firstname(self) -> str:
        return self.model.firstname

    @property
    def required_sub_object_id(self) -> UUID:
        return self.model.required_sub_object_id

    async def gen_required_sub_object(self) -> EntTestSubObject:
        return await EntTestSubObject.genx(self.vc, self.model.required_sub_object_id)

    @property
    def username(self) -> str:
        """
        This is the username that you will use on the platform.
        """
        return self.model.username

    @property
    def city(self) -> str | None:
        return self.model.city

    @property
    def context(self) -> str | None:
        return self.model.context

    @property
    def lastname(self) -> str | None:
        return self.model.lastname

    @property
    def optional_sub_object_id(self) -> UUID | None:
        return self.model.optional_sub_object_id

    async def gen_optional_sub_object(self) -> EntTestSubObject | None:
        if self.model.optional_sub_object_id:
            return await EntTestSubObject.gen(
                self.vc, self.model.optional_sub_object_id
            )
        return None

    @property
    def optional_sub_object_no_ex_id(self) -> UUID | None:
        return self.model.optional_sub_object_no_ex_id

    async def gen_optional_sub_object_no_ex(self) -> EntTestSubObject | None:
        if self.model.optional_sub_object_no_ex_id:
            return await EntTestSubObject.gen(
                self.vc, self.model.optional_sub_object_no_ex_id
            )
        return None

    @property
    def self_id(self) -> UUID | None:
        return self.model.self_id

    async def gen_self(self) -> EntTestObject | None:
        if self.model.self_id:
            return await EntTestObject.gen(self.vc, self.model.self_id)
        return None

    @property
    def status(self) -> Status | None:
        return self.model.status

    @property
    def status_code(self) -> int | None:
        return self.model.status_code

    @property
    def when_is_it_cool(self) -> datetime | None:
        return self.model.when_is_it_cool

    @classmethod
    async def genx(cls, vc: ExampleViewerContext, ent_id: UUID) -> EntTestObject:
        ent = await cls.gen(vc, ent_id)
        if not ent:
            raise ValueError(f"No EntTestObject found for ID {ent_id}")
        return ent

    @classmethod
    async def gen(cls, vc: ExampleViewerContext, ent_id: UUID) -> EntTestObject | None:
        session = get_session()
        model = await session.get(EntTestObjectModel, ent_id)
        return await cls._gen_from_model(vc, model)

    @classmethod
    async def gen_from_username(
        cls, vc: ExampleViewerContext, username: str
    ) -> EntTestObject | None:
        session = get_session()
        result = await session.execute(
            select(EntTestObjectModel).where(EntTestObjectModel.username == username)
        )
        model = result.scalar_one_or_none()
        return await cls._gen_from_model(vc, model)

    @classmethod
    async def genx_from_username(
        cls, vc: ExampleViewerContext, username: str
    ) -> EntTestObject:
        result = await cls.gen_from_username(vc, username)
        if not result:
            raise ValueError(f"No EntTestObject found for username {username}")
        return result

    @classmethod
    async def _gen_from_model(
        cls, vc: ExampleViewerContext, model: EntTestObjectModel | None
    ) -> EntTestObject | None:
        if not model:
            return None
        ent = EntTestObject(vc=vc, model=model)
        # TODO check privacy here
        return ent

    @classmethod
    async def _genx_from_model(
        cls, vc: ExampleViewerContext, model: EntTestObjectModel
    ) -> EntTestObject:
        ent = EntTestObject(vc=vc, model=model)
        # TODO check privacy here
        return ent

    @classmethod
    def query(cls, vc: ExampleViewerContext) -> EntTestObjectQuery:
        return EntTestObjectQuery(vc=vc)


class EntTestObjectQuery:
    vc: ExampleViewerContext
    query: Select[tuple[EntTestObjectModel]]

    def __init__(self, vc: ExampleViewerContext) -> None:
        self.vc = vc
        self.query = select(EntTestObjectModel)

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

    async def gen(self) -> list[EntTestObject]:
        session = get_session()
        result = await session.execute(self.query)
        models = result.scalars().all()
        ents = [await EntTestObject._gen_from_model(self.vc, model) for model in models]
        return list(filter(None, ents))

    async def gen_first(self) -> EntTestObject | None:
        session = get_session()
        result = await session.execute(self.query.limit(1))
        model = result.scalar_one_or_none()
        return await EntTestObject._gen_from_model(self.vc, model)


class EntTestObjectMutator:
    @classmethod
    def create(
        cls,
        vc: ExampleViewerContext,
        a_good_thing: str,
        firstname: str,
        required_sub_object_id: UUID,
        username: str,
        city: str | None = None,
        context: str | None = None,
        lastname: str | None = None,
        optional_sub_object_id: UUID | None = None,
        optional_sub_object_no_ex_id: UUID | None = None,
        self_id: UUID | None = None,
        status: Status | None = None,
        status_code: int | None = None,
        when_is_it_cool: datetime | None = None,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> EntTestObjectMutatorCreationAction:
        return EntTestObjectMutatorCreationAction(
            vc=vc,
            id=id,
            created_at=created_at,
            a_good_thing=a_good_thing,
            firstname=firstname,
            required_sub_object_id=required_sub_object_id,
            username=username,
            city=city,
            context=context,
            lastname=lastname,
            optional_sub_object_id=optional_sub_object_id,
            optional_sub_object_no_ex_id=optional_sub_object_no_ex_id,
            self_id=self_id,
            status=status,
            status_code=status_code,
            when_is_it_cool=when_is_it_cool,
        )

    @classmethod
    def update(
        cls, vc: ExampleViewerContext, ent: EntTestObject
    ) -> EntTestObjectMutatorUpdateAction:
        return EntTestObjectMutatorUpdateAction(vc=vc, ent=ent)

    @classmethod
    def delete(
        cls, vc: ExampleViewerContext, ent: EntTestObject
    ) -> EntTestObjectMutatorDeletionAction:
        return EntTestObjectMutatorDeletionAction(vc=vc, ent=ent)


class EntTestObjectMutatorCreationAction:
    vc: ExampleViewerContext
    id: UUID
    a_good_thing: str
    firstname: str
    required_sub_object_id: UUID
    username: str
    city: str | None = None
    context: str | None = None
    lastname: str | None = None
    optional_sub_object_id: UUID | None = None
    optional_sub_object_no_ex_id: UUID | None = None
    self_id: UUID | None = None
    status: Status | None = None
    status_code: int | None = None
    when_is_it_cool: datetime | None = None

    def __init__(
        self,
        vc: ExampleViewerContext,
        id: UUID | None,
        created_at: datetime | None,
        a_good_thing: str,
        firstname: str,
        required_sub_object_id: UUID,
        username: str,
        city: str | None,
        context: str | None,
        lastname: str | None,
        optional_sub_object_id: UUID | None,
        optional_sub_object_no_ex_id: UUID | None,
        self_id: UUID | None,
        status: Status | None,
        status_code: int | None,
        when_is_it_cool: datetime | None,
    ) -> None:
        self.vc = vc
        self.created_at = created_at if created_at else datetime.now(tz=UTC)
        self.id = id if id else generate_uuid(EntTestObject, self.created_at)
        self.a_good_thing = a_good_thing
        self.firstname = firstname
        self.required_sub_object_id = required_sub_object_id
        self.username = username
        self.city = city
        self.context = context
        self.lastname = lastname
        self.optional_sub_object_id = optional_sub_object_id
        self.optional_sub_object_no_ex_id = optional_sub_object_no_ex_id
        self.self_id = self_id
        self.status = status
        self.status_code = status_code
        self.when_is_it_cool = when_is_it_cool

    async def gen_savex(self) -> EntTestObject:
        session = get_session()
        model = EntTestObjectModel(
            id=self.id,
            created_at=self.created_at,
            a_good_thing=self.a_good_thing,
            firstname=self.firstname,
            required_sub_object_id=self.required_sub_object_id,
            username=self.username,
            city=self.city,
            context=self.context,
            lastname=self.lastname,
            optional_sub_object_id=self.optional_sub_object_id,
            optional_sub_object_no_ex_id=self.optional_sub_object_no_ex_id,
            self_id=self.self_id,
            status=self.status,
            status_code=self.status_code,
            when_is_it_cool=self.when_is_it_cool,
        )
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await EntTestObject._genx_from_model(self.vc, model)


class EntTestObjectMutatorUpdateAction:
    vc: ExampleViewerContext
    ent: EntTestObject
    id: UUID
    a_good_thing: str
    firstname: str
    required_sub_object_id: UUID
    username: str
    city: str | None = None
    context: str | None = None
    lastname: str | None = None
    optional_sub_object_id: UUID | None = None
    optional_sub_object_no_ex_id: UUID | None = None
    self_id: UUID | None = None
    status: Status | None = None
    status_code: int | None = None
    when_is_it_cool: datetime | None = None

    def __init__(self, vc: ExampleViewerContext, ent: EntTestObject) -> None:
        self.vc = vc
        self.ent = ent
        self.a_good_thing = ent.a_good_thing
        self.firstname = ent.firstname
        self.required_sub_object_id = ent.required_sub_object_id
        self.username = ent.username
        self.city = ent.city
        self.context = ent.context
        self.lastname = ent.lastname
        self.optional_sub_object_id = ent.optional_sub_object_id
        self.optional_sub_object_no_ex_id = ent.optional_sub_object_no_ex_id
        self.self_id = ent.self_id
        self.status = ent.status
        self.status_code = ent.status_code
        self.when_is_it_cool = ent.when_is_it_cool

    async def gen_savex(self) -> EntTestObject:
        session = get_session()
        model = self.ent.model
        model.a_good_thing = self.a_good_thing
        model.firstname = self.firstname
        model.required_sub_object_id = self.required_sub_object_id
        model.username = self.username
        model.city = self.city
        model.context = self.context
        model.lastname = self.lastname
        model.optional_sub_object_id = self.optional_sub_object_id
        model.optional_sub_object_no_ex_id = self.optional_sub_object_no_ex_id
        model.self_id = self.self_id
        model.status = self.status
        model.status_code = self.status_code
        model.when_is_it_cool = self.when_is_it_cool
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await EntTestObject._genx_from_model(self.vc, model)


class EntTestObjectMutatorDeletionAction:
    vc: ExampleViewerContext
    ent: EntTestObject

    def __init__(self, vc: ExampleViewerContext, ent: EntTestObject) -> None:
        self.vc = vc
        self.ent = ent

    async def gen_save(self) -> None:
        session = get_session()
        model = self.ent.model
        # TODO privacy checks
        await session.delete(model)
        await session.flush()


class EntTestObjectExample:
    @classmethod
    async def gen_create(
        cls,
        vc: ExampleViewerContext,
        created_at: datetime | None = None,
        a_good_thing: str | Sentinel = NOTHING,
        firstname: str | Sentinel = NOTHING,
        required_sub_object_id: UUID | Sentinel = NOTHING,
        username: str | Sentinel = NOTHING,
        city: str | None = None,
        context: str | None = None,
        lastname: str | None = None,
        optional_sub_object_id: UUID | None = None,
        optional_sub_object_no_ex_id: UUID | None = None,
        self_id: UUID | None = None,
        status: Status | None = None,
        status_code: int | None = None,
        when_is_it_cool: datetime | None = None,
    ) -> EntTestObject:
        # TODO make sure we only use this in test mode

        a_good_thing = (
            "A sunny day" if isinstance(a_good_thing, Sentinel) else a_good_thing
        )

        firstname = "Vincent" if isinstance(firstname, Sentinel) else firstname

        if (
            isinstance(required_sub_object_id, Sentinel)
            or required_sub_object_id is None
        ):
            required_sub_object_id_ent = await EntTestSubObjectExample.gen_create(vc)
            required_sub_object_id = required_sub_object_id_ent.id

        if isinstance(username, Sentinel):
            field = cls._get_field("username")
            if not isinstance(field, FieldWithDynamicExample):
                raise TypeError(
                    "Internal ent error: "
                    + f"field {field.name} must support dynamic examples."
                )
            generator = field.get_example_generator()
            if generator:
                username = generator()

        city = "Los Angeles" if isinstance(city, Sentinel) else city

        context = (
            "This is some good context." if isinstance(context, Sentinel) else context
        )

        if (
            isinstance(optional_sub_object_id, Sentinel)
            or optional_sub_object_id is None
        ):
            optional_sub_object_id_ent = await EntTestSubObjectExample.gen_create(vc)
            optional_sub_object_id = optional_sub_object_id_ent.id
        status = Status.HAPPY if isinstance(status, Sentinel) else status

        status_code = 404 if isinstance(status_code, Sentinel) else status_code

        if isinstance(when_is_it_cool, Sentinel):
            field = cls._get_field("when_is_it_cool")
            if not isinstance(field, FieldWithDynamicExample):
                raise TypeError(
                    "Internal ent error: "
                    + f"field {field.name} must support dynamic examples."
                )
            generator = field.get_example_generator()
            if generator:
                when_is_it_cool = generator()

        return await EntTestObjectMutator.create(
            vc=vc,
            created_at=created_at,
            a_good_thing=a_good_thing,
            firstname=firstname,
            required_sub_object_id=required_sub_object_id,
            username=username,
            city=city,
            context=context,
            lastname=lastname,
            optional_sub_object_id=optional_sub_object_id,
            optional_sub_object_no_ex_id=optional_sub_object_no_ex_id,
            self_id=self_id,
            status=status,
            status_code=status_code,
            when_is_it_cool=when_is_it_cool,
        ).gen_savex()

    @classmethod
    def _get_field(cls, field_name: str) -> Field:
        schema = EntTestObjectSchema()
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
