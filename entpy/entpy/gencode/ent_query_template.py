def generate() -> str:
    return """from abc import ABC, abstractmethod
from typing import Generic, Self, TypeVar, Any
from sqlalchemy import Select, Table
from entpy.framework.ent import Ent
from sqlalchemy.sql.expression import ColumnElement

from .ent_model import EntModel

ENT = TypeVar("ENT", bound=Ent)
ENTMODEL = TypeVar("ENTMODEL")


class EntQuery[ENT, ENTMODEL](ABC):
    query: Select[tuple[ENTMODEL]]

    def join(self, model_class: type[EntModel] | Table, predicate: ColumnElement[bool]) -> Self:
        self.query = self.query.join(model_class, predicate)
        return self

    def where(self, predicate: ColumnElement[bool]) -> Self:
        self.query = self.query.where(predicate)
        return self

    def order_by(self, predicate: ColumnElement[Any]) -> Self:
        self.query = self.query.order_by(predicate)
        return self

    @abstractmethod
    def order_by_id_asc(self) -> Self:
        pass

    @abstractmethod
    def order_by_id_desc(self) -> Self:
        pass

    def limit(self, limit: int) -> Self:
        self.query = self.query.limit(limit)
        return self

    def offset(self, offset: int) -> Self:
        self.query = self.query.offset(offset)
        return self

    @abstractmethod
    async def gen(self) -> list[ENT]:
        pass

    @abstractmethod
    async def gen_first(self) -> ENT | None:
        pass

    @abstractmethod
    async def genx_first(self) -> ENT:
        pass

    @abstractmethod
    async def gen_count_NO_PRIVACY(self) -> int:
        pass
"""  # noqa: E501
