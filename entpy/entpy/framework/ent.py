from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self, TypeVar
from uuid import UUID

from entpy.framework.action import Action
from entpy.framework.database import db, emulate_for_update
from entpy.framework.decision import Decision
from entpy.framework.errors import EntNotFoundError
from entpy.framework.id_factory import validate_ent_id
from entpy.framework.model import ModelMixin
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)
ENTMODEL = TypeVar("ENTMODEL", bound=ModelMixin)
if TYPE_CHECKING:
    from entpy.framework.query import EntQuery


class Ent[VC, ENTMODEL]:
    model: ENTMODEL
    m: type[ENTMODEL]
    vc: VC

    # Model fields are actually returned by __getattr__()
    if TYPE_CHECKING:
        id: UUID
        created_at: datetime
        updated_at: datetime
        soft_deleted_at: datetime | None
    else:

        def __getattr__(self, name: str) -> Any:
            if not name.startswith("_"):
                return getattr(self.model, name)
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def __init__(self, vc: VC, model: ENTMODEL) -> None:
        self.vc = vc
        self.model = model

    @abstractmethod
    async def _gen_evaluate_privacy(
        self, vc: VC, action: Action, default_to_deny: bool = True
    ) -> Decision:
        pass

    @classmethod
    @abstractmethod
    async def gen(
        cls, vc: VC, ent_id: UUID | str, for_update: bool = False
    ) -> Self | None:
        pass

    @classmethod
    async def genx(cls, vc: VC, ent_id: UUID | str, for_update: bool = False) -> Self:
        ent = await cls.gen(vc, ent_id, for_update)
        if not ent:
            raise EntNotFoundError(f"No {cls.__name__} found for ID {{ent_id}}")
        return ent

    @classmethod
    @abstractmethod
    async def _gen_no_privacy_DO_NOT_USE(  # noqa: N802
        cls, vc: VC, ent_id: UUID | str, for_update: bool = False
    ) -> Self | None:
        pass

    @classmethod
    async def _genx_no_privacy_DO_NOT_USE(  # noqa: N802
        cls, vc: VC, ent_id: UUID | str, for_update: bool = False
    ) -> Self:
        ent = await cls._gen_no_privacy_DO_NOT_USE(vc, ent_id, for_update)
        if ent is None:
            raise EntNotFoundError(f"No {cls.__name__} found for ID {{ent_id}}")
        return ent

    @classmethod
    async def _gen_from_model(cls, vc: VC, model: ENTMODEL | None) -> Self | None:
        if not model:
            return None
        ent = cls(vc=vc, model=model)
        decision = await ent._gen_evaluate_privacy(vc=vc, action=Action.READ)
        return ent if decision == Decision.ALLOW else None

    @classmethod
    async def _genx_from_model(cls, vc: VC, model: ENTMODEL) -> Self:
        ent = await cls._gen_from_model(vc=vc, model=model)
        if not ent:
            raise EntNotFoundError(f"No {cls.__name__} found for ID {{model.id}}")
        return ent

    @classmethod
    @abstractmethod
    def query(cls, vc: VC) -> "EntQuery[Self, ENTMODEL]":
        pass


class EntObjectBase(Ent[VC, ENTMODEL]):
    @classmethod
    async def gen(
        cls, vc: VC, ent_id: UUID | str, for_update: bool = False
    ) -> Self | None:
        real_ent_id = validate_ent_id(ent_id)
        async with emulate_for_update(cls.m, "id", real_ent_id, for_update):
            model = await db.session.get(
                cls.m, real_ent_id, with_for_update=for_update or None
            )
        db.session.info.setdefault("cache", set()).add(model)
        return await cls._gen_from_model(vc, model)  # noqa: SLF001

    @classmethod
    async def _gen_no_privacy_DO_NOT_USE(  # noqa: N802
        cls, vc: VC, ent_id: UUID | str, for_update: bool = False
    ) -> Self | None:
        real_ent_id = validate_ent_id(ent_id)
        model = await db.session.get(
            cls.m, real_ent_id, with_for_update=for_update or None
        )
        if model is None:
            return None
        db.session.info.setdefault("cache", set()).add(model)
        return cls(vc=vc, model=model)
