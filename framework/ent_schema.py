from abc import ABC, abstractmethod

from framework.ent_field import EntField


class EntSchema(ABC):
    @abstractmethod
    def get_fields(self) -> list[EntField]:
        pass
