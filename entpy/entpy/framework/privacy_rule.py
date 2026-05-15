from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from entpy.framework.database import db
from entpy.framework.decision import Decision

if TYPE_CHECKING:
    from entpy.framework.ent import Ent, EntPending
    from entpy.framework.viewer_context import ViewerContext


class PrivacyRule[VC: ViewerContext, T: Ent, P: EntPending](ABC):
    @abstractmethod
    async def gen_evaluate(
        self, vc: VC, ent: T, pending_ent: P | None = None
    ) -> Decision:
        pass

    # This should return the field values which are inspected during evaluation.
    # Subsequent ents with the same values will use the cached decision.
    def cache_key(self, ent: T) -> Any:
        return None

    async def gen_evaluate_cached(
        self,
        vc: VC,
        ent: T,
        pending_ent: P | None = None,
    ) -> Decision:
        ent_key = self.cache_key(ent)
        if ent_key is None:
            return await self.gen_evaluate(vc, ent, pending_ent)

        full_key = (type(self), id(vc), ent_key)
        result = db.session.info.setdefault("privacy", {}).get(full_key)
        if result is None:
            result = await self.gen_evaluate(vc, ent, pending_ent)
            db.session.info["privacy"][full_key] = result

        return result  # type: ignore[no-any-return]


@dataclass
class EdgeDelegate:
    edge_name: str
