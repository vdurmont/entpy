from abc import ABC, abstractmethod
from hashlib import sha256

from entpy import Action, EdgeDelegate, PrivacyRule
from entpy.framework.composite_index import CompositeIndex
from entpy.framework.descriptor import Descriptor


class Schema(Descriptor, ABC):
    @abstractmethod
    def get_privacy_config(
        self, action: Action
    ) -> list[EdgeDelegate | PrivacyRule]:
        pass

    def get_composite_indexes(self) -> list[CompositeIndex]:
        return []

    def is_immutable(self) -> bool:
        return False

    @classmethod
    def get_uuid_type(cls) -> bytes:
        base_name = cls.__name__.replace("Schema", "")
        return sha256(base_name.encode()).digest()[:2]
