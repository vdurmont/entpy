from functools import cache

from entpy import Action, DenyIfSoftDeleted, PrivacyRule

from rules import AllowIfOmniscientViewerContext, AllowIfTestViewerContext


class PrivacyMixin:
    @classmethod
    @cache
    def _get_prepended_rules(cls, action: Action) -> list[PrivacyRule]:
        prepended_rules: list[PrivacyRule] = [AllowIfTestViewerContext()]

        if action == Action.READ:
            prepended_rules.append(AllowIfOmniscientViewerContext())
            prepended_rules.append(DenyIfSoftDeleted())

        return prepended_rules
