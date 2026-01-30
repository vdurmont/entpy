from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.scoping import async_scoped_session

from entpy.framework.action import Action
from entpy.framework.decision import Decision
from entpy.framework.ent import Ent
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)
T = TypeVar("T", bound=Ent)


class PrivacyRule(ABC, Generic[VC, T]):
    @abstractmethod
    async def gen_evaluate(self, vc: VC, ent: T) -> Decision:
        pass

    def cache_key(self, ent: T) -> Any:
        return ent.id

    async def gen_evaluate_cached(
        self,
        session: async_scoped_session | AsyncSession,
        vc: VC,
        action: Action,
        ent: T,
    ) -> Decision:
        ent_key = self.cache_key(ent)
        if ent_key is None:
            return await self.gen_evaluate(vc, ent)

        full_key = (type(self), id(vc), action, ent_key)
        result = session.info.setdefault("privacy", {}).get(full_key)
        if result is None:
            result = await self.gen_evaluate(vc, ent)
            session.info["privacy"][full_key] = result

        return result  # type: ignore[no-any-return]


@dataclass
class EdgeDelegate:
    edge_name: str
