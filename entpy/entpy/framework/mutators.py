from abc import abstractmethod
from datetime import UTC, datetime
from typing import TypeVar

from entpy.framework.action import Action
from entpy.framework.database import db
from entpy.framework.decision import Decision
from entpy.framework.ent import EntObjectBase
from entpy.framework.errors import PrivacyError, ValidationError
from entpy.framework.model import ModelMixin
from entpy.framework.schema import Schema
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC")
ENT = TypeVar("ENT")
ENTMODEL = TypeVar("ENTMODEL")


class EntMutatorAction:
    schema: Schema

    def _validate(self) -> None:
        for field in self.schema.get_all_fields():
            for validator in field._validators:
                if not validator.validate(getattr(self, field.name)):
                    raise ValidationError(f"Field {field.name} is invalid")


class EntMutatorCreationAction[
    VC: ViewerContext,
    ENT: EntObjectBase,
    ENTMODEL: ModelMixin,
](EntMutatorAction):
    ent_type: type[ENT]
    vc: VC

    @abstractmethod
    def _create_model(self) -> ENTMODEL:
        pass

    async def gen_savex(self) -> ENT:
        self._validate()
        model = self._create_model()
        db.session.add(model)
        ent = self.ent_type(vc=self.vc, model=model)
        decision = await ent.gen_evaluate_privacy(vc=self.vc, action=Action.CREATE)
        if decision != Decision.ALLOW:
            raise PrivacyError(
                f"Current viewer context is not authorized to CREATE {self.ent_type.__name__} with ID {ent.id}"
            )
        await db.session.flush()
        return await self.ent_type._genx_from_model(self.vc, model)  # noqa: SLF001


class EntMutatorUpdateAction[
    VC: ViewerContext,
    ENT: EntObjectBase,
    ENTMODEL: ModelMixin,
](EntMutatorAction):
    ent_type: type[ENT]
    ent: ENT
    vc: VC

    @abstractmethod
    def _update_model(self, model: ENTMODEL) -> ENTMODEL:
        pass

    async def gen_savex(self) -> ENT:
        self._validate()
        model = self._update_model(self.ent.model)
        db.session.add(model)
        new_ent = self.ent_type(vc=self.vc, model=model)
        decision = await new_ent.gen_evaluate_privacy(vc=self.vc, action=Action.UPDATE)
        if decision != Decision.ALLOW:
            raise PrivacyError(
                f"Current viewer context is not authorized to UPDATE {self.ent_type.__name__} with ID {new_ent.id}"
            )
        await db.session.flush()
        await db.session.refresh(model)
        return await self.ent_type._genx_from_model(self.vc, model)  # noqa: SLF001


class EntMutatorDeletionAction[
    VC: ViewerContext,
    ENT: EntObjectBase,
    ENTMODEL: ModelMixin,
]:
    ent_type: type[ENT]
    ent: ENT
    vc: VC

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
