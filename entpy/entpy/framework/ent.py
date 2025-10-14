from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, Self, TypeVar
from uuid import UUID

from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)


class Ent(ABC, Generic[VC]):
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

    @classmethod
    @abstractmethod
    async def gen(cls, vc: VC, ent_id: UUID) -> Self | None:
        pass

    @classmethod
    @abstractmethod
    async def genx(cls, vc: VC, ent_id: UUID) -> Self:
        pass
