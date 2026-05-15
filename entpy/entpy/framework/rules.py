from typing import TypeVar

from entpy.framework.decision import Decision
from entpy.framework.ent import Ent, EntPending
from entpy.framework.privacy_rule import PrivacyRule
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC", bound=ViewerContext)
T = TypeVar("T", bound=Ent)
P = TypeVar("P", bound=EntPending)


class AllowAll(PrivacyRule[VC, T, P]):
    async def gen_evaluate(
        self, vc: VC, ent: T, pending_ent: P | None = None
    ) -> Decision:
        return Decision.ALLOW


class DenyAll(PrivacyRule[VC, T, P]):
    async def gen_evaluate(
        self, vc: VC, ent: T, pending_ent: P | None = None
    ) -> Decision:
        return Decision.DENY


class AllOf(PrivacyRule[VC, T, P]):
    rules: list[PrivacyRule]

    def __init__(self, rules: list[PrivacyRule]) -> None:
        if len(rules) == 0:
            raise ValueError("Cannot call `AllOf` rule with no rule to evaluate.")
        self.rules = rules

    async def gen_evaluate(
        self, vc: VC, ent: T, pending_ent: P | None = None
    ) -> Decision:
        for rule in self.rules:
            decision = await rule.gen_evaluate(vc, ent, pending_ent)
            if decision != Decision.ALLOW:
                return Decision.DENY
        return Decision.ALLOW
