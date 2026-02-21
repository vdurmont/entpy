from typing import TypeVar

from entpy.framework.decision import Decision
from entpy.framework.ent import Ent
from entpy.framework.privacy_rule import PrivacyRule
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)
T = TypeVar("T", bound=Ent)


class DenyIfSoftDeleted(PrivacyRule[VC, T]):
    async def gen_evaluate(self, _vc: VC, ent: T) -> Decision:
        return Decision.DENY if ent.soft_deleted_at else Decision.PASS
