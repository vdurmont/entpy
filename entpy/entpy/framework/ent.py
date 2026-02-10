import logging
from abc import abstractmethod
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any, Self, TypeVar
from uuid import UUID

from sqlalchemy import select

from entpy.framework.action import Action
from entpy.framework.database import db, emulate_for_update
from entpy.framework.decision import Decision
from entpy.framework.errors import EntNotFoundError, ExecutionError
from entpy.framework.id_factory import validate_ent_id
from entpy.framework.model import ModelMixin
from entpy.framework.privacy_rule import EdgeDelegate, PrivacyRule
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC")
ENTMODEL = TypeVar("ENTMODEL")
if TYPE_CHECKING:
    from entpy.framework.query import EntQuery
    from entpy.framework.schema import Schema

privacy_logger = logging.getLogger("entpy.privacy")


class EntMeta(type):
    if not TYPE_CHECKING:
        # Hide this from mypy otherwise it thinks any attribute is valid
        def __getattr__(cls, name: str) -> Any:
            if name.startswith("gen_from_"):
                return partial(cls._gen_from_unique, name[9:])

            if name.startswith("genx_from_"):
                return partial(cls._genx_from_unique, name[10:])

            raise AttributeError(f"'{cls.__name__}' object has no attribute '{name}'")


class Ent[VC: ViewerContext, ENTMODEL: ModelMixin](metaclass=EntMeta):
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
        # Hide this from mypy otherwise it thinks any attribute is valid
        def __getattr__(self, name: str) -> Any:
            if name.startswith("gen_"):
                return partial(self._gen_edge, name[4:])

            if not name.startswith("_"):
                return getattr(self.model, name)

            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def __init__(self, vc: VC, model: ENTMODEL) -> None:
        self.vc = vc
        self.model = model

    @classmethod
    @abstractmethod
    def _get_edge_type(
        cls, edge_name: str
    ) -> tuple[type["Ent[ViewerContext, ModelMixin]"], bool]:
        raise ValueError(f"Unknown edge for {cls.__name__}: {edge_name}")

    @abstractmethod
    async def gen_evaluate_privacy(
        self,
        vc: VC,
        action: Action,
        default_to_deny: bool = True,
        log_on_deny: bool = True,
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
    async def _gen_from_unique(
        cls, name: str, vc: VC, value: Any, for_update: bool = False
    ) -> Self | None:
        pass

    @classmethod
    async def _genx_from_unique(
        cls, name: str, vc: VC, value: Any, for_update: bool = False
    ) -> Self | None:
        ent = await cls._gen_from_unique(name, vc, value, for_update)
        if not ent:
            raise EntNotFoundError(f"No {cls.__name__} found for {name} {{value}}")
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

    async def _gen_edge(
        self, edge_name: str
    ) -> "Ent[ViewerContext, ModelMixin] | None":
        edge_id = getattr(self.model, f"{edge_name}_id")
        ent_type, nullable = self._get_edge_type(edge_name)
        if not nullable:
            return await ent_type.genx(self.vc, edge_id)
        elif edge_id:
            return await ent_type.gen(self.vc, edge_id)
        else:
            return None


class EntObjectBase[VC: ViewerContext, ENTMODEL: ModelMixin](Ent[VC, ENTMODEL]):
    schema: "Schema"

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

    @classmethod
    async def _gen_from_model(cls, vc: VC, model: ENTMODEL | None) -> Self | None:
        if not model:
            return None
        ent = cls(vc=vc, model=model)
        decision = await ent.gen_evaluate_privacy(vc=vc, action=Action.READ)
        return ent if decision == Decision.ALLOW else None

    @classmethod
    async def _genx_from_model(cls, vc: VC, model: ENTMODEL) -> Self:
        ent = await cls._gen_from_model(vc=vc, model=model)
        if not ent:
            raise EntNotFoundError(f"No {cls.__name__} found for ID {{model.id}}")
        return ent

    @classmethod
    async def _gen_from_unique(
        cls, name: str, vc: VC, value: Any, for_update: bool = False
    ) -> Self | None:
        query = select(cls.m).where(getattr(cls.m, name) == value)
        if for_update:
            query = query.with_for_update()
        async with emulate_for_update(cls.m, name, value, for_update):
            result = await db.session.execute(query)
        model = result.scalar_one_or_none()
        db.session.info.setdefault("cache", set()).add(model)
        return await cls._gen_from_model(vc, model)  # noqa: SLF001

    @classmethod
    @abstractmethod
    def _get_prepended_rules(cls, action: Action) -> list[PrivacyRule]:
        pass

    async def gen_evaluate_privacy(
        self,
        vc: VC,
        action: Action,
        default_to_deny: bool = True,
        log_on_deny: bool = True,
    ) -> Decision:
        # Build the complete list: prepended rules + entity's config
        all_rules = self._get_prepended_rules(action) + self.schema.get_privacy_config(
            action
        )

        # Evaluate each rule/delegate in order
        for item in all_rules:
            if isinstance(item, PrivacyRule):
                decision = await item.gen_evaluate_cached(vc, self)
                if decision == Decision.DENY and log_on_deny:
                    privacy_logger.debug(
                        "Rule %s denied %s of %s %s for %s",
                        item.__class__.__name__,
                        str(action),
                        self.__class__.__name__,
                        self.id,
                        str(vc),
                    )
            elif isinstance(item, EdgeDelegate):
                edge_type = self._get_edge_type(item.edge_name)[0]
                delegate = await edge_type._genx_no_privacy_DO_NOT_USE(
                    vc, getattr(self, f"{item.edge_name}_id")
                )
                decision = await delegate.gen_evaluate_privacy(
                    vc, action, default_to_deny=False
                )
                if decision == Decision.DENY and log_on_deny:
                    privacy_logger.debug(
                        "Delegate %s denied %s of %s %s for %s",
                        item.edge_name,
                        str(action),
                        self.__class__.__name__,
                        self.id,
                        str(vc),
                    )
            else:
                raise ExecutionError(
                    f"An invalid privacy configuration was found for {self.__class__.__name__}: invalid item type in list",
                )
            # If we get an ALLOW or DENY, we return instantly. Else, we keep going.
            if decision != Decision.PASS:
                return decision

        # Return based on default behavior
        if default_to_deny:
            if log_on_deny:
                privacy_logger.debug(
                    "Default denied %s of %s %s for %s",
                    str(action),
                    self.__class__.__name__,
                    self.id,
                    str(vc),
                )
            return Decision.DENY
        return Decision.PASS

    @classmethod
    @abstractmethod
    def query(cls, vc: VC) -> "EntQuery[VC, Self, ENTMODEL, ENTMODEL]":
        pass


class EntPatternBase[VC: ViewerContext, ENTMODEL: ModelMixin](Ent[VC, ENTMODEL]):
    @classmethod
    @abstractmethod
    def _get_child_type(cls, uuid_type: bytes) -> type[Self]:
        pass

    @classmethod
    async def _gen_no_privacy_DO_NOT_USE(  # noqa: N802
        cls, vc: VC, ent_id: UUID | str, for_update: bool = False
    ) -> Self | None:
        real_ent_id = validate_ent_id(ent_id)
        ent_type = cls._get_child_type(real_ent_id.bytes[6:8])
        return await ent_type._gen_no_privacy_DO_NOT_USE(vc, ent_id, for_update)

    @classmethod
    async def gen(
        cls, vc: VC, ent_id: UUID | str, for_update: bool = False
    ) -> Self | None:
        real_ent_id = validate_ent_id(ent_id)
        ent_type = cls._get_child_type(real_ent_id.bytes[6:8])
        return await ent_type.gen(vc, ent_id, for_update)

    @classmethod
    async def _gen_from_unique(
        cls, name: str, vc: VC, value: Any, for_update: bool = False
    ) -> Self | None:
        query = select(cls.m.id).where(getattr(cls.m, name) == value)
        result = await db.session.execute(query)
        ent_id = result.scalar_one_or_none()
        if ent_id is None:
            return None
        ent_type = cls._get_child_type(ent_id.bytes[6:8])
        return await ent_type.gen(vc, ent_id, for_update)

    @classmethod
    @abstractmethod
    def query(cls, vc: VC) -> "EntQuery[VC, Self, ENTMODEL, UUID]":
        pass
