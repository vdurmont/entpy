from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self, TypeVar
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
