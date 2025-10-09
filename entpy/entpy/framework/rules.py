from typing import TypeVar

from entpy.framework.decision import Decision
from entpy.framework.ent import Ent
from entpy.framework.privacy_rule import PrivacyRule
from entpy.framework.viewer_context import ViewerContext

T = TypeVar("T", bound=Ent)


class AllowAll(PrivacyRule):
    async def gen_evaluate(self, vc: ViewerContext, ent: T) -> Decision:
        return Decision.ALLOW
