from abc import ABC, abstractmethod
from collections import defaultdict
from hashlib import md5
from typing import Any, ClassVar, Self, TypeVar
from uuid import UUID

from sqlalchemy import Select, Table, func, select
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm.strategy_options import _AbstractLoad
from sqlalchemy.sql.expression import ColumnElement
from werkzeug.exceptions import NotFound

from entpy.framework.database import db
from entpy.framework.ent import Ent, EntObjectBase, EntPatternBase
from entpy.framework.errors import EntNotFoundError, ExecutionError
from entpy.framework.model import ModelMixin
from entpy.framework.viewer_context import ViewerContext

QUERY_CACHE_THRESHOLD = 100

VC = TypeVar("VC")
ENT = TypeVar("ENT")
ENTMODEL = TypeVar("ENTMODEL")
TARGET = TypeVar("TARGET")


class EntQuery[
    VC: ViewerContext,
    ENT: Ent,
    ENTMODEL: ModelMixin,
    TARGET: ModelMixin | UUID,
](ABC):
    ent_type: ClassVar[type[ENT]]
    model_type: ClassVar[type[ENTMODEL]]
    include_soft_deleted: bool = False
    query: Select[tuple[TARGET]]
    vc: VC

    @abstractmethod
    def __init__(
        self,
        vc: VC,
        query: Select[tuple[TARGET]] | None = None,
        include_soft_deleted: bool = False,
    ) -> None:
        pass

    def join(
        self, model_class: type[ModelMixin] | Table, predicate: ColumnElement[bool]
    ) -> Self:
        query = self.query.join(model_class, predicate)
        return self.__class__(self.vc, query, self.include_soft_deleted)

    def where(self, predicate: ColumnElement[bool]) -> Self:
        query = self.query.where(predicate)
        return self.__class__(self.vc, query, self.include_soft_deleted)

    def order_by(self, predicate: ColumnElement[Any]) -> Self:
        query = self.query.order_by(predicate)
        return self.__class__(self.vc, query, self.include_soft_deleted)

    def order_by_id_asc(self) -> Self:
        query = self.query.order_by(self.model_type.id.asc())
        return self.__class__(self.vc, query, self.include_soft_deleted)

    def order_by_id_desc(self) -> Self:
        query = self.query.order_by(self.model_type.id.desc())
        return self.__class__(self.vc, query, self.include_soft_deleted)

    def limit(self, limit: int | None) -> Self:
        query = self.query.limit(limit)
        return self.__class__(self.vc, query, self.include_soft_deleted)

    def offset(self, offset: int) -> Self:
        query = self.query.offset(offset)
        return self.__class__(self.vc, query, self.include_soft_deleted)

    def options(self, options: _AbstractLoad) -> Self:
        query = self.query.options(options)
        return self.__class__(self.vc, query, self.include_soft_deleted)

    def with_soft_deleted(self) -> Self:
        return self.__class__(self.vc, self.query, include_soft_deleted=True)

    def _finalize_query(self) -> Select[tuple[TARGET]]:
        if self.include_soft_deleted:
            return self.query
        else:
            return self.query.where(self.model_type.soft_deleted_at.is_(None))

    @abstractmethod
    async def _gen_ents(self, rows: list[TARGET]) -> list[ENT | None]:
        pass

    @abstractmethod
    async def _gen_ent(self, rows: list[TARGET]) -> ENT | None:
        pass

    async def _gen_cached(
        self, query: Select[tuple[TARGET]], for_update: bool = False
    ) -> list[TARGET]:
        compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
        key = md5(compiled.encode()).digest()
        if not for_update and (cached := db.session.info.get("query", {}).get(key)):
            return cached  # type: ignore[no-any-return]

        rows = list(await db.session.scalars(query))
        if len(rows) < QUERY_CACHE_THRESHOLD:
            db.session.info.setdefault("query", {})[key] = rows
        return rows

    async def gen(self, for_update: bool = False) -> list[ENT]:
        query = (
            self._finalize_query().with_for_update()
            if for_update
            else self._finalize_query()
        )
        result = await self._gen_cached(query, for_update)
        ents = await self._gen_ents(result)
        return list(filter(None, ents))

    async def gen_first(self, for_update: bool = False) -> ENT | None:
        query = self._finalize_query().limit(1)
        if for_update:
            query = query.with_for_update()
        result = await self._gen_cached(query, for_update)
        return await self._gen_ent(result)

    async def genx_first(self, for_update: bool = False) -> ENT:
        ent = await self.gen_first(for_update)
        if not ent:
            if self.query._whereclause is not None:
                where = f" for {self.query._whereclause.compile(compile_kwargs={"include_table": False, "literal_binds": True})}"
            else:
                where = ""
            raise EntNotFoundError(f"No {self.ent_type.__name__} found{where}")
        return ent

    async def genx_first_or_404(self, for_update: bool = False) -> ENT:
        try:
            return await self.genx_first(for_update)
        except EntNotFoundError as e:
            raise NotFound from e

    async def gen_count_NO_PRIVACY(self) -> int:  # noqa: N802
        count_query = (
            self._finalize_query()
            .with_only_columns(func.count(), maintain_column_froms=True)
            .order_by(None)
        )
        count = await db.session.scalar(count_query)
        if count is None:
            raise ExecutionError("Unable to get the count")
        return count

    async def gen_count(self, privacy_threshold: int = 50) -> int:  # noqa: N802
        count = await self.gen_count_NO_PRIVACY()
        if count <= privacy_threshold:
            # We have just a few ents, let's load them and check privacy
            # to make sure our count is more accurate.
            fetch_query = self._finalize_query().limit(None).offset(None)
            result = await self._gen_cached(fetch_query)
            ents = await self._gen_ents(result)
            return len(list(filter(None, ents)))

        return count


class EntObjectQuery[VC: ViewerContext, ENT: EntObjectBase, ENTMODEL: ModelMixin](
    EntQuery[VC, ENT, ENTMODEL, ENTMODEL]
):
    def __init__(
        self,
        vc: VC,
        query: Select[tuple[ENTMODEL]] | None = None,
        include_soft_deleted: bool = False,
    ) -> None:
        self.vc = vc
        self.query = select(self.model_type) if query is None else query
        self.include_soft_deleted = include_soft_deleted

    async def _gen_ents(self, rows: list[ENTMODEL]) -> list[ENT | None]:
        return [
            await self.ent_type._gen_from_model(self.vc, model)  # noqa: SLF001
            for model in rows
        ]

    async def _gen_ent(self, rows: list[ENTMODEL]) -> ENT | None:
        if len(rows) > 1:
            raise MultipleResultsFound(
                "Multiple rows were found when one or none was required"
            )
        if rows:
            return await self.ent_type._gen_from_model(self.vc, rows[0])  # noqa: SLF001
        return None


class EntPatternQuery[
    VC: ViewerContext,
    ENT: EntPatternBase,
    ENTMODEL: ModelMixin,
](EntQuery[VC, ENT, ENTMODEL, UUID]):
    def __init__(
        self,
        vc: VC,
        query: Select[tuple[UUID]] | None = None,
        include_soft_deleted: bool = False,
    ) -> None:
        self.vc = vc
        self.query = select(self.model_type.id) if query is None else query
        self.include_soft_deleted = include_soft_deleted

    async def _gen_ents(self, rows: list[UUID]) -> list[ENT | None]:
        ids_by_type = defaultdict(list)
        for ent_id in rows:
            ids_by_type[ent_id.bytes[6:8]].append(ent_id)

        all_ents = {}
        for uuid_type, ids in ids_by_type.items():
            ent_type = self.ent_type._get_child_type(uuid_type)
            for ent in (
                await ent_type.query(self.vc)
                .where(ent_type.m.id.in_(ids))
                .limit(None)
                .gen()
            ):
                all_ents[ent.id] = ent

        return [all_ents[ent_id] for ent_id in rows if ent_id in all_ents]

    async def _gen_ent(self, rows: list[UUID]) -> ENT | None:
        if len(rows) > 1:
            raise MultipleResultsFound(
                "Multiple rows were found when one or none was required"
            )
        if rows:
            ent_type = self.ent_type._get_child_type(rows[0].bytes[6:8])
            return await ent_type.gen(self.vc, rows[0])
        return None
