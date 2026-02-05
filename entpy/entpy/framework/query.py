from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, ClassVar, Self, TypeVar
from uuid import UUID

from sqlalchemy import Result, Select, Table, func, select
from sqlalchemy.orm.strategy_options import _AbstractLoad
from sqlalchemy.sql.expression import ColumnElement

from entpy.framework.database import db
from entpy.framework.ent import Ent, EntObjectBase, EntPatternBase
from entpy.framework.errors import EntNotFoundError, ExecutionError
from entpy.framework.model import ModelMixin
from entpy.framework.viewer_context import ViewerContext

VC = TypeVar("VC")
ENT = TypeVar("ENT")
ENTMODEL = TypeVar("ENTMODEL")


class EntQuery[VC: ViewerContext, ENT: Ent, ENTMODEL: ModelMixin](ABC):
    ent_type: ClassVar[type[ENT]]
    model_type: ClassVar[type[ENTMODEL]]
    include_soft_deleted: bool = False
    query: Select[tuple[ENTMODEL]]
    vc: VC

    def join(
        self, model_class: type[ModelMixin] | Table, predicate: ColumnElement[bool]
    ) -> Self:
        self.query = self.query.join(model_class, predicate)
        return self

    def where(self, predicate: ColumnElement[bool]) -> Self:
        self.query = self.query.where(predicate)
        return self

    def order_by(self, predicate: ColumnElement[Any]) -> Self:
        self.query = self.query.order_by(predicate)
        return self

    def order_by_id_asc(self) -> Self:
        self.query = self.query.order_by(self.model_type.id.asc())
        return self

    def order_by_id_desc(self) -> Self:
        self.query = self.query.order_by(self.model_type.id.desc())
        return self

    def limit(self, limit: int | None) -> Self:
        self.query = self.query.limit(limit)
        return self

    def offset(self, offset: int) -> Self:
        self.query = self.query.offset(offset)
        return self

    def options(self, options: _AbstractLoad) -> Self:
        self.query = self.query.options(options)
        return self

    def with_soft_deleted(self) -> Self:
        self.include_soft_deleted = True
        return self

    def _finalize_query(self) -> Select[tuple[ENTMODEL]]:
        if self.include_soft_deleted:
            return self.query
        else:
            return self.query.where(self.model_type.soft_deleted_at.is_(None))

    @abstractmethod
    async def _gen_ents(self, result: Result[tuple[ENTMODEL]]) -> list[ENT | None]:
        pass

    @abstractmethod
    async def _gen_ent(self, result: Result[tuple[ENTMODEL]]) -> ENT | None:
        pass

    async def gen(self, for_update: bool = False) -> list[ENT]:
        query = (
            self._finalize_query().with_for_update()
            if for_update
            else self._finalize_query()
        )
        result = await db.session.execute(query)
        ents = await self._gen_ents(result)
        return list(filter(None, ents))

    async def gen_first(self, for_update: bool = False) -> ENT | None:
        query = self._finalize_query().limit(1)
        if for_update:
            query = query.with_for_update()
        result = await db.session.execute(query)
        return await self._gen_ent(result)

    async def genx_first(self, for_update: bool = False) -> ENT:
        ent = await self.gen_first(for_update)
        if not ent:
            raise EntNotFoundError(
                f"Expected to find a {self.ent_type.__name__}, got None."
            )
        return ent

    async def gen_count_NO_PRIVACY(self, force_no_privacy: bool = False) -> int:  # noqa: N802
        count_query = (
            self._finalize_query()
            .with_only_columns(func.count(), maintain_column_froms=True)
            .order_by(None)
        )
        count_result = await db.session.execute(count_query)
        count = count_result.scalar()
        if count is None:
            raise ExecutionError("Unable to get the count")

        if count <= 50 and not force_no_privacy:
            # We have just a few ents, let's load them and check privacy
            # to make sure our count is more accurate.
            fetch_query = self._finalize_query().limit(None).offset(None)
            result = await db.session.execute(fetch_query)
            ents = await self._gen_ents(result)
            return len(list(filter(None, ents)))

        return count


class EntObjectQuery[VC: ViewerContext, ENT: EntObjectBase, ENTMODEL: ModelMixin](
    EntQuery[VC, ENT, ENTMODEL]
):
    def __init__(self, vc: VC) -> None:
        self.vc = vc
        self.query = select(self.model_type)

    async def _gen_ents(self, result: Result[tuple[ENTMODEL]]) -> list[ENT | None]:
        models = result.scalars().all()
        return [
            await self.ent_type._gen_from_model(self.vc, model)  # noqa: SLF001
            for model in models
        ]

    async def _gen_ent(self, result: Result[tuple[ENTMODEL]]) -> ENT | None:
        model = result.scalar_one_or_none()
        return await self.ent_type._gen_from_model(self.vc, model)  # noqa: SLF001


class EntPatternQuery[
    VC: ViewerContext,
    ENT: EntPatternBase,
    ENTMODEL: ModelMixin,
](EntQuery[VC, ENT, ENTMODEL]):
    def __init__(self, vc: VC) -> None:
        self.vc = vc
        self.query = select(self.model_type.id)

    async def _gen_ents(self, result: Result[tuple[UUID]]) -> list[ENT | None]:  # type: ignore[override]
        ent_ids = result.scalars().all()
        ids_by_type = defaultdict(list)
        for ent_id in ent_ids:
            ids_by_type[ent_id.bytes[6:8]].append(ent_id)

        all_ents = {}
        for uuid_type, ids in ids_by_type.items():
            ent_type = self.ent_type.get_child_type(uuid_type)
            for ent in (
                await ent_type.query(self.vc)
                .where(ent_type.m.id.in_(ids))
                .limit(None)
                .gen()
            ):
                all_ents[ent.id] = ent

        return [all_ents[ent_id] for ent_id in ent_ids if ent_id in all_ents]

    async def _gen_ent(self, result: Result[tuple[UUID]]) -> ENT | None:  # type: ignore[override]
        ent_id = result.scalar_one_or_none()
        if not ent_id:
            return None
        ent_type = self.ent_type.get_child_type(ent_id.bytes[6:8])
        return await ent_type.gen(self.vc, ent_id)
