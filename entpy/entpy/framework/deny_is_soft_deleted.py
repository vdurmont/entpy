from typing import TypeVar

from entpy.framework.decision import Decision
from entpy.framework.ent import Ent, EntPending
from entpy.framework.privacy_rule import PrivacyRule
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)
T = TypeVar("T", bound=Ent)
P = TypeVar("P", bound=EntPending)


class DenyIfSoftDeleted(PrivacyRule[VC, T, P]):
    async def gen_evaluate(
        self, _vc: VC, ent: T, pending_ent: P | None = None
    ) -> Decision:
        return Decision.DENY if ent.soft_deleted_at else Decision.PASS
