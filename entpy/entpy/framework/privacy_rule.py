from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from entpy.framework.decision import Decision
from entpy.framework.ent import Ent
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)
T = TypeVar("T", bound=Ent)


class PrivacyRule(ABC, Generic[VC, T]):
    @abstractmethod
    async def gen_evaluate(self, vc: VC, ent: T) -> Decision:
        pass
