from functools import cache

from entpy import Action, PrivacyRule

from rules import AllowIfTestViewerContext
from rules import AllowIfOmniscientViewerContext
from rules import DenyIfSoftDeleted


class PrivacyMixin:
    @classmethod
    @cache
    def _get_prepended_rules(cls, action: Action) -> list[PrivacyRule]:
        prepended_rules: list[PrivacyRule] = [AllowIfTestViewerContext()]

        if action == Action.READ:
            prepended_rules.append(AllowIfOmniscientViewerContext())
            prepended_rules.append(DenyIfSoftDeleted())

        return prepended_rules
