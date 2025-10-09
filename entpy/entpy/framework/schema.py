from abc import ABC, abstractmethod

from entpy import Action, PrivacyRule
from entpy.framework.descriptor import Descriptor


class Schema(Descriptor, ABC):
    @abstractmethod
    def get_privacy_rules(self, action: Action) -> list[PrivacyRule]:
        pass
