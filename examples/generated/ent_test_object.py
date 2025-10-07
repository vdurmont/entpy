from __future__ import annotations
from entpy import ViewerContext, Ent
from uuid import UUID, uuid4
from datetime import datetime

from database import get_session
from .ent_test_thing import IEntTestThing
from sqlalchemy.dialects.postgresql import UUID as DBUUID
from ent_test_object_schema import EntTestObjectSchema
from sqlalchemy.orm import Mapped, mapped_column
from sentinels import NOTHING, Sentinel  # type: ignore
from .ent_model import EntModel
from entpy import Field, FieldWithDynamicExample
from .ent_test_sub_object import EntTestSubObjectExample
from sqlalchemy import select
from sqlalchemy import ForeignKey, String
from .ent_test_sub_object import EntTestSubObject


class EntTestObjectModel(EntModel):
    __tablename__ = "test_object"

    a_good_thing: Mapped[str] = mapped_column(String(100), nullable=False)
    firstname: Mapped[str] = mapped_column(String(100), nullable=False)
    required_sub_object_id: Mapped[UUID] = mapped_column(
        DBUUID(as_uuid=True), ForeignKey("test_sub_object.id"), nullable=False
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lastname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    optional_sub_object_id: Mapped[UUID | None] = mapped_column(
        DBUUID(as_uuid=True), ForeignKey("test_sub_object.id"), nullable=True
    )
    optional_sub_object_no_ex_id: Mapped[UUID | None] = mapped_column(
        DBUUID(as_uuid=True), ForeignKey("test_sub_object.id"), nullable=True
    )


class EntTestObject(Ent, IEntTestThing):
    vc: ViewerContext
    model: EntTestObjectModel

    def __init__(self, vc: ViewerContext, model: EntTestObjectModel) -> None:
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
        return self.model.username

    @property
    def city(self) -> str | None:
        return self.model.city

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

    @classmethod
    async def genx(cls, vc: ViewerContext, ent_id: UUID) -> EntTestObject:
        ent = await cls.gen(vc, ent_id)
        if not ent:
            raise ValueError(f"No EntTestObject found for ID {ent_id}")
        return ent

    @classmethod
    async def gen(cls, vc: ViewerContext, ent_id: UUID) -> EntTestObject | None:
        session = get_session()
        model = await session.get(EntTestObjectModel, ent_id)
        return await cls._gen_from_model(vc, model)

    @classmethod
    async def gen_from_username(
        cls, vc: ViewerContext, username: str
    ) -> EntTestObject | None:
        session = get_session()
        result = await session.execute(
            select(EntTestObjectModel).where(EntTestObjectModel.username == username)
        )
        model = result.scalar_one_or_none()
        return await cls._gen_from_model(vc, model)

    @classmethod
    async def genx_from_username(
        cls, vc: ViewerContext, username: str
    ) -> EntTestObject:
        result = await cls.gen_from_username(vc, username)
        if not result:
            raise ValueError(f"No EntTestObject found for username {username}")
        return result

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
        a_good_thing: str,
        firstname: str,
        required_sub_object_id: UUID,
        username: str,
        city: str | None = None,
        lastname: str | None = None,
        optional_sub_object_id: UUID | None = None,
        optional_sub_object_no_ex_id: UUID | None = None,
    ) -> EntTestObjectMutatorCreationAction:
        return EntTestObjectMutatorCreationAction(
            vc=vc,
            a_good_thing=a_good_thing,
            firstname=firstname,
            required_sub_object_id=required_sub_object_id,
            username=username,
            city=city,
            lastname=lastname,
            optional_sub_object_id=optional_sub_object_id,
            optional_sub_object_no_ex_id=optional_sub_object_no_ex_id,
        )

    @classmethod
    def update(
        cls, vc: ViewerContext, ent: EntTestObject
    ) -> EntTestObjectMutatorUpdateAction:
        return EntTestObjectMutatorUpdateAction(vc=vc, ent=ent)

    @classmethod
    def delete(
        cls, vc: ViewerContext, ent: EntTestObject
    ) -> EntTestObjectMutatorDeletionAction:
        return EntTestObjectMutatorDeletionAction(vc=vc, ent=ent)


class EntTestObjectMutatorCreationAction:
    vc: ViewerContext
    id: UUID
    a_good_thing: str
    firstname: str
    required_sub_object_id: UUID
    username: str
    city: str | None = None
    lastname: str | None = None
    optional_sub_object_id: UUID | None = None
    optional_sub_object_no_ex_id: UUID | None = None

    def __init__(
        self,
        vc: ViewerContext,
        a_good_thing: str,
        firstname: str,
        required_sub_object_id: UUID,
        username: str,
        city: str | None,
        lastname: str | None,
        optional_sub_object_id: UUID | None,
        optional_sub_object_no_ex_id: UUID | None,
    ) -> None:
        self.vc = vc
        self.id = uuid4()
        self.a_good_thing = a_good_thing
        self.firstname = firstname
        self.required_sub_object_id = required_sub_object_id
        self.username = username
        self.city = city
        self.lastname = lastname
        self.optional_sub_object_id = optional_sub_object_id
        self.optional_sub_object_no_ex_id = optional_sub_object_no_ex_id

    async def gen_savex(self) -> EntTestObject:
        session = get_session()
        model = EntTestObjectModel(
            id=self.id,
            a_good_thing=self.a_good_thing,
            firstname=self.firstname,
            required_sub_object_id=self.required_sub_object_id,
            username=self.username,
            city=self.city,
            lastname=self.lastname,
            optional_sub_object_id=self.optional_sub_object_id,
            optional_sub_object_no_ex_id=self.optional_sub_object_no_ex_id,
        )
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await EntTestObject._genx_from_model(self.vc, model)


class EntTestObjectMutatorUpdateAction:
    vc: ViewerContext
    ent: EntTestObject
    id: UUID
    a_good_thing: str
    firstname: str
    required_sub_object_id: UUID
    username: str
    city: str | None = None
    lastname: str | None = None
    optional_sub_object_id: UUID | None = None
    optional_sub_object_no_ex_id: UUID | None = None

    def __init__(self, vc: ViewerContext, ent: EntTestObject) -> None:
        self.vc = vc
        self.ent = ent
        self.a_good_thing = ent.a_good_thing
        self.firstname = ent.firstname
        self.required_sub_object_id = ent.required_sub_object_id
        self.username = ent.username
        self.city = ent.city
        self.lastname = ent.lastname
        self.optional_sub_object_id = ent.optional_sub_object_id
        self.optional_sub_object_no_ex_id = ent.optional_sub_object_no_ex_id

    async def gen_savex(self) -> EntTestObject:
        session = get_session()
        model = self.ent.model
        model.a_good_thing = self.a_good_thing
        model.firstname = self.firstname
        model.required_sub_object_id = self.required_sub_object_id
        model.username = self.username
        model.city = self.city
        model.lastname = self.lastname
        model.optional_sub_object_id = self.optional_sub_object_id
        model.optional_sub_object_no_ex_id = self.optional_sub_object_no_ex_id
        session.add(model)
        await session.flush()
        # TODO privacy checks
        return await EntTestObject._genx_from_model(self.vc, model)


class EntTestObjectMutatorDeletionAction:
    vc: ViewerContext
    ent: EntTestObject

    def __init__(self, vc: ViewerContext, ent: EntTestObject) -> None:
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
        vc: ViewerContext,
        a_good_thing: str | Sentinel = NOTHING,
        firstname: str | Sentinel = NOTHING,
        required_sub_object_id: UUID | Sentinel = NOTHING,
        username: str | Sentinel = NOTHING,
        city: str | None = None,
        lastname: str | None = None,
        optional_sub_object_id: UUID | None = None,
        optional_sub_object_no_ex_id: UUID | None = None,
    ) -> EntTestObject:
        # TODO make sure we only use this in test mode

        a_good_thing = (
            "A sunny day" if isinstance(a_good_thing, Sentinel) else a_good_thing
        )

        firstname = "Vincent" if isinstance(firstname, Sentinel) else firstname

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

        optional_sub_object_id_ent = await EntTestSubObjectExample.gen_create(vc)
        optional_sub_object_id = optional_sub_object_id_ent.id

        return await EntTestObjectMutator.create(
            vc=vc,
            a_good_thing=a_good_thing,
            firstname=firstname,
            required_sub_object_id=required_sub_object_id,
            username=username,
            city=city,
            lastname=lastname,
            optional_sub_object_id=optional_sub_object_id,
            optional_sub_object_no_ex_id=optional_sub_object_no_ex_id,
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
