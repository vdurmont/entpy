from typing import TypeVar

from entpy.framework.decision import Decision
from entpy.framework.ent import Ent
from entpy.framework.privacy_rule import PrivacyRule
from entpy.framework.viewer_context import ViewerContext

T = TypeVar("T", bound=Ent)


class AllowAll(PrivacyRule):
    async def gen_evaluate(self, vc: ViewerContext, ent: T) -> Decision:
        return Decision.ALLOW


class AllOf(PrivacyRule):
    rules: list[PrivacyRule]

    def __init__(self, rules: list[PrivacyRule]) -> None:
        if len(rules) == 0:
            raise ValueError("Cannot call `AllOf` rule with no rule to evaluate.")
        self.rules = rules

    async def gen_evaluate(self, vc: ViewerContext, ent: T) -> Decision:
        for rule in self.rules:
            decision = await rule.gen_evaluate(vc, ent)
            if decision != Decision.ALLOW:
                return Decision.DENY
        return Decision.ALLOW
