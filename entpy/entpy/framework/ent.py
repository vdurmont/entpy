from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Self, TypeVar
from uuid import UUID

from entpy.framework.action import Action
from entpy.framework.decision import Decision
from entpy.framework.model import ModelMixin
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)
ENTMODEL = TypeVar("ENTMODEL", bound=ModelMixin)
if TYPE_CHECKING:
    from entpy.framework.query import EntQuery


class Ent[VC, ENTMODEL]:
    model: ENTMODEL
    m: type[ENTMODEL]

    @property
    @abstractmethod
    def id(self) -> UUID:
        pass

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        pass

    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        pass

    @property
    @abstractmethod
    def soft_deleted_at(self) -> datetime | None:
        pass

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
    @abstractmethod
    async def genx(cls, vc: VC, ent_id: UUID | str, for_update: bool = False) -> Self:
        pass

    @classmethod
    @abstractmethod
    def query(cls, vc: VC) -> "EntQuery[Self, ENTMODEL]":
        pass
