from entpy.framework.descriptor import Descriptor
from entpy.framework.pattern import Pattern
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import ImportedObject


def generate(
    descriptor: Descriptor,
    base_name: str,
    vc: ImportedObject,
    threshold_to_stop_loading_ents_for_count: int,
) -> GeneratedContent:
    is_pattern = isinstance(descriptor, Pattern)
    i = "I" if is_pattern else ""

    imports = [
        "from sqlalchemy.sql.expression import ColumnElement",
        "from typing import Any, TypeVar",
        "from sqlalchemy import select, Select, func, Result",
        "from entpy import EntNotFoundError, ExecutionError",
        "from entpy.framework.query import EntQuery",
    ]

    if is_pattern:
        imports.append("from typing import cast")
        imports.append("from collections import defaultdict")

    gen_count = _generate_gen_count(
        threshold_to_stop_loading_ents_for_count=threshold_to_stop_loading_ents_for_count,
    )

    query_target = f"{base_name}Model.id" if is_pattern else f"{base_name}Model"

    gen_ents = _generate_gen_ents(is_pattern=is_pattern, base_name=base_name)
    gen_ent = _generate_gen_ent(is_pattern=is_pattern, base_name=base_name)
    gen_single_ent = _generate_gen_single_ent(
        is_pattern=is_pattern, base_name=base_name
    )
    order_by_methods = _generate_order_by_methods(
        is_pattern=is_pattern, base_name=base_name
    )
    generic = "UUID" if is_pattern else f"{base_name}Model"
    column_holder = f"{base_name}Model" if is_pattern else f"{base_name}Model"

    return GeneratedContent(
        imports=imports + gen_count.imports,
        code=f"""
T = TypeVar("T")

class {i}{base_name}Query(EntQuery[{i}{base_name}, {generic}]):
    vc: {vc.name}
    include_soft_deleted: bool = False

    def __init__(self, vc: {vc.name}) -> None:
        self.vc = vc
        self.query = select({query_target})

    async def gen(self, for_update: bool = False) -> list[{i}{base_name}]:
        query = self._finalize_query().with_for_update() if for_update else self._finalize_query()
        result = await db.session.execute(query)
        ents = await self._gen_ents(result)
        return list(filter(None, ents))

    def _finalize_query(self) -> Select:
        if self.include_soft_deleted:
            return self.query
        else:
            return self.query.where({column_holder}.soft_deleted_at.is_(None))

{gen_ents}

    async def gen_first(self, for_update: bool = False) -> {i}{base_name} | None:
        query = self._finalize_query().limit(1)
        if for_update:
            query = query.with_for_update()
        result = await db.session.execute(query)
        return await self._gen_ent(result)

{gen_ent}

{gen_single_ent}

    async def genx_first(self, for_update: bool = False) -> {i}{base_name}:
        ent = await self.gen_first(for_update)
        if not ent:
            raise EntNotFoundError(f"Expected to find a {base_name}, got None.")
        return ent

{gen_count.code}

{order_by_methods}

    def with_soft_deleted(self) -> "{i}{base_name}Query":
        self.include_soft_deleted = True
        return self
""",  # noqa: E501
    )


def _generate_gen_ents(is_pattern: bool, base_name: str) -> str:
    i = "I" if is_pattern else ""
    if is_pattern:
        return f"""
    async def _gen_ents(self, result: Result[tuple[UUID]]) -> list[{i}{base_name} | None]:
        from .all_models import UUID_TO_ENT

        ent_ids = result.scalars().all()
        ids_by_type = defaultdict(list)
        for ent_id in ent_ids:
            ids_by_type[ent_id.bytes[6:8]].append(ent_id)

        all_ents = {"{}"}
        for uuid_type, ids in ids_by_type.items():
            ent_type = UUID_TO_ENT[uuid_type]
            for ent in (
                await ent_type.query(self.vc)
                .where(ent_type.m.id.in_(ids))
                .limit(None)
                .gen()
            ):
                all_ents[ent.id] = ent

        return [cast(I{base_name}, all_ents[ent_id]) for ent_id in ent_ids if ent_id in all_ents]
"""  # noqa: E501
    return f"""
    async def _gen_ents(self, result: Result[tuple[{base_name}Model]]) -> list[{i}{base_name} | None]:
        models = result.scalars().all()
        return [
            await {base_name}._gen_from_model(self.vc, model)  # noqa: SLF001
            for model in models
        ]
"""  # noqa: E501


def _generate_gen_ent(is_pattern: bool, base_name: str) -> str:
    i = "I" if is_pattern else ""
    if is_pattern:
        return f"""
    async def _gen_ent(self, result: Result[tuple[UUID]]) -> {i}{base_name} | None:
        ent_id = result.scalar_one_or_none()
        if not ent_id:
            return None
        return await self._gen_single_ent(ent_id)
"""
    return f"""
    async def _gen_ent(self, result: Result[tuple[{base_name}Model]]) -> {i}{base_name} | None:
        model = result.scalar_one_or_none()
        return await {i}{base_name}._gen_from_model(self.vc, model)  # noqa: SLF001
"""  # noqa: E501


def _generate_gen_single_ent(is_pattern: bool, base_name: str) -> str:
    i = "I" if is_pattern else ""
    if is_pattern:
        return f"""
    async def _gen_single_ent(self, ent_id: UUID) -> {i}{base_name} | None:
        from .all_models import UUID_TO_ENT
        uuid_type = ent_id.bytes[6:8]
        ent_type = UUID_TO_ENT[uuid_type]
        # Casting is ok here, the id always inherits {i}{base_name}
        return await cast(type[{i}{base_name}], ent_type).gen(self.vc, ent_id)
"""
    return ""


def _generate_order_by_methods(is_pattern: bool, base_name: str) -> str:
    i = "I" if is_pattern else ""
    if is_pattern:
        # For patterns, we order by the id column in the view's table
        return f"""
    def order_by_id_asc(self) -> "{i}{base_name}Query":
        self.query = self.query.order_by({base_name}Model.id.asc())
        return self

    def order_by_id_desc(self) -> "{i}{base_name}Query":
        self.query = self.query.order_by({base_name}Model.id.desc())
        return self
"""
    else:
        # For regular models, we order by the model's id column
        return f"""
    def order_by_id_asc(self) -> "{i}{base_name}Query":
        self.query = self.query.order_by({base_name}Model.id.asc())
        return self

    def order_by_id_desc(self) -> "{i}{base_name}Query":
        self.query = self.query.order_by({base_name}Model.id.desc())
        return self
"""


def _generate_gen_count(
    threshold_to_stop_loading_ents_for_count: int,
) -> GeneratedContent:
    ent_loader = ""
    if threshold_to_stop_loading_ents_for_count > 0:
        ent_loader = f"""
        if count <= {threshold_to_stop_loading_ents_for_count} and not force_no_privacy:
            # We have just a few ents, let's load them and check privacy
            # to make sure our count is more accurate.
            fetch_query = self._finalize_query().limit(None).offset(None)
            result = await db.session.execute(fetch_query)
            ents = await self._gen_ents(result)
            return len(list(filter(None, ents)))
"""
    return GeneratedContent(
        code=f"""
    async def gen_count_NO_PRIVACY(self, force_no_privacy: bool = False) -> int:
        count_query = self._finalize_query().with_only_columns(func.count(), maintain_column_froms=True).order_by(None)
        result = await db.session.execute(count_query)
        count = result.scalar()
        if count is None:
            raise ExecutionError("Unable to get the count"){ent_loader}
        return count"""
    )
