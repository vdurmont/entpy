from abc import ABC, abstractmethod

from entpy import Action, PrivacyRule
from entpy.framework.composite_index import CompositeIndex
from entpy.framework.descriptor import Descriptor


class Schema(Descriptor, ABC):
    @abstractmethod
    def get_privacy_rules(self, action: Action) -> list[PrivacyRule]:
        pass

    def get_composite_indexes(self) -> list[CompositeIndex]:
        return []

    def is_immutable(self) -> bool:
        return False
