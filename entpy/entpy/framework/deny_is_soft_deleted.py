from typing import TYPE_CHECKING, TypeVar

from entpy.framework.decision import Decision
from entpy.framework.ent import Ent
from entpy.framework.privacy_rule import PrivacyRule
from entpy.framework.viewer_context import ViewerContext

if TYPE_CHECKING:
    from entpy.framework.ent import EntPending

VC = TypeVar("VC", bound=ViewerContext)
T = TypeVar("T", bound=Ent)


class DenyIfSoftDeleted(PrivacyRule[VC, T]):
    async def gen_evaluate(
        self, _vc: VC, ent: T, pending_ent: "EntPending | None" = None
    ) -> Decision:
        return Decision.DENY if ent.soft_deleted_at else Decision.PASS
