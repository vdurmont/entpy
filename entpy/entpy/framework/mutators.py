import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from werkzeug.exceptions import Forbidden

from entpy.framework.action import Action
from entpy.framework.database import db
from entpy.framework.decision import Decision
from entpy.framework.ent import EntObjectBase, generate_ent_id
from entpy.framework.errors import PrivacyError, ValidationError
from entpy.framework.fields.email_field import EmailField
from entpy.framework.model import ModelMixin
from entpy.framework.schema import Schema
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC")
ENT = TypeVar("ENT")
ENTMODEL = TypeVar("ENTMODEL")

log = logging.getLogger(__name__)


class EntMutatorAction[VC: ViewerContext, ENT: EntObjectBase, ENTMODEL: ModelMixin]:
    ent_type: type[ENT]
    model_type: type[ENTMODEL]
    model: ENTMODEL
    schema: Schema
    vc: VC

    if not TYPE_CHECKING:

        def __setattr__(self, name: str, value: Any) -> None:
            if hasattr(self, "model") and name in self.model.__table__.columns:
                # Normalize email fields
                if hasattr(self, "schema"):
                    for field in self.schema.get_all_fields():
                        if field.name == name and isinstance(field, EmailField):
                            value = field.normalize(value)
                            break
                setattr(self.model, name, value)
            else:
                super().__setattr__(name, value)

    def _validate(self) -> None:
        for field in self.schema.get_all_fields():
            for validator in field._validators:
                if not validator.validate(getattr(self.model, field.name)):
                    raise ValidationError(f"Field {field.name} is invalid")

    def record_events(self) -> None:
        for descriptor in [self.schema] + self.schema.get_patterns():
            if fields := descriptor.get_event_fields():
                payload = {field: getattr(self.model, field) for field in fields}
                db.session.info.setdefault("events", []).append(
                    (descriptor.get_table_name(), payload)
                )


class EntMutatorCreationAction[
    VC: ViewerContext,
    ENT: EntObjectBase,
    ENTMODEL: ModelMixin,
](EntMutatorAction[VC, ENT, ENTMODEL]):
    def __init__(
        self,
        vc: VC,
        id: UUID | None,
        created_at: datetime | None,
        updated_at: datetime | None,
        **kwargs: Any,
    ) -> None:
        self.vc = vc
        created_at = created_at if created_at else datetime.now(tz=UTC)

        # Normalize email field values before creating the model
        for field in self.schema.get_all_fields():
            if isinstance(field, EmailField) and field.name in kwargs:
                kwargs[field.name] = field.normalize(kwargs[field.name])

        self.model = self.model_type(
            id=id if id else generate_ent_id(self.schema.__class__, created_at),  # type: ignore[call-arg]
            created_at=created_at,
            updated_at=updated_at if updated_at else created_at,
            **kwargs,
        )

    async def gen_savex(self) -> ENT:
        self._validate()
        db.session.add(self.model)
        ent = self.ent_type(vc=self.vc, model=self.model)
        decision = await ent.gen_evaluate_privacy(vc=self.vc, action=Action.CREATE)
        if decision != Decision.ALLOW:
            raise PrivacyError(
                f"Current viewer context is not authorized to CREATE {self.ent_type.__name__} with ID {ent.id}"
            )
        await db.session.flush()
        self.record_events()
        return await self.ent_type._genx_from_model(self.vc, self.model)  # noqa: SLF001

    async def gen_savex_or_403(self) -> ENT:
        try:
            return await self.gen_savex()
        except PrivacyError as e:
            raise Forbidden(str(e)) from e


class EntMutatorUpdateAction[
    VC: ViewerContext,
    ENT: EntObjectBase,
    ENTMODEL: ModelMixin,
](EntMutatorAction[VC, ENT, ENTMODEL]):
    ent: ENT

    def __init__(self, vc: VC, ent: ENT) -> None:
        self.vc = vc
        self.ent = ent
        self.model = ent.model

    async def gen_savex(self) -> ENT:
        self._validate()
        db.session.add(self.model)
        decision = await self.ent.gen_evaluate_privacy(vc=self.vc, action=Action.UPDATE)
        if decision != Decision.ALLOW:
            raise PrivacyError(
                f"Current viewer context is not authorized to UPDATE {self.ent_type.__name__} with ID {self.ent.id}"
            )
        await db.session.flush()
        await db.session.refresh(self.model)
        self.record_events()
        return self.ent

    async def gen_savex_or_403(self) -> ENT:
        try:
            return await self.gen_savex()
        except PrivacyError as e:
            raise Forbidden(str(e)) from e


class EntMutatorDeletionAction[
    VC: ViewerContext,
    ENT: EntObjectBase,
    ENTMODEL: ModelMixin,
]:
    ent_type: type[ENT]
    ent: ENT

    def __init__(self, vc: VC, ent: ENT, is_soft_delete: bool) -> None:
        self.vc = vc
        self.ent = ent
        self.is_soft_delete = is_soft_delete

    async def gen_save(self) -> None:
        model = self.ent.model
        action = Action.SOFT_DELETE if self.is_soft_delete else Action.HARD_DELETE
        decision = await self.ent.gen_evaluate_privacy(vc=self.vc, action=action)
        if decision != Decision.ALLOW:
            raise PrivacyError(
                f"Current viewer context is not authorized to {action.value} {self.ent_type.__name__} with ID {self.ent.id}"
            )
        if self.is_soft_delete:
            model.soft_deleted_at = datetime.now(tz=UTC)
            model.updated_at = datetime.now(tz=UTC)
            db.session.add(model)
        else:
            await db.session.delete(model)
        await db.session.flush()

    async def gen_save_or_403(self) -> None:
        try:
            await self.gen_save()
        except PrivacyError as e:
            raise Forbidden(str(e)) from e
