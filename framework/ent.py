from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class Ent(ABC):
    @property
    @abstractmethod
    def id(self) -> UUID:
        pass

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        pass

    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        pass
