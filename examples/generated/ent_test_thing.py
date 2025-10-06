from __future__ import annotations

from abc import ABC, abstractmethod


class IEntTestThing(ABC):
    @property
    @abstractmethod
    def a_good_thing(self) -> str:
        pass
