from entpy.framework.descriptor import Descriptor
from entpy.framework.pattern import Pattern
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


def generate(
    descriptor: Descriptor, base_name: str, session_getter_fn_name: str, vc_name: str
) -> GeneratedContent:
    is_pattern = isinstance(descriptor, Pattern)
    i = "I" if is_pattern else ""

    imports = [
        "from sqlalchemy.sql.expression import ColumnElement",
        "from typing import Any, TypeVar, Generic",
        "from sqlalchemy import select, Select, func, Result",
        "from entpy import EntNotFoundError, ExecutionError",
        "from .ent_query import EntQuery",
    ]

    if is_pattern:
        imports.append("from typing import cast")

    # For patterns, we need to import and use the view
    query_target = f"{base_name}View.id" if is_pattern else f"{base_name}Model"
    view_import = (
        f"from .{to_snake_case(base_name)}_view import {base_name}View"
        if is_pattern
        else ""
    )

    gen_ents = _generate_gen_ents(is_pattern=is_pattern, base_name=base_name)
    gen_ent = _generate_gen_ent(is_pattern=is_pattern, base_name=base_name)
    gen_single_ent = _generate_gen_single_ent(
        is_pattern=is_pattern, base_name=base_name
    )
    order_by_methods = _generate_order_by_methods(
        is_pattern=is_pattern, base_name=base_name
    )
    generic = "UUID" if is_pattern else f"{base_name}Model"

    return GeneratedContent(
        imports=imports,
        code=f"""
T = TypeVar("T")

class {i}{base_name}Query(EntQuery[{i}{base_name}, {generic}]):
    vc: {vc_name}

    def __init__(self, vc: {vc_name}) -> None:
        self.vc = vc
        {view_import}
        self.query = select({query_target})

    async def gen(self) -> list[{i}{base_name}]:
        session = {session_getter_fn_name}()
        result = await session.execute(self.query)
        ents = await self._gen_ents(result)
        return list(filter(None, ents))

{gen_ents}

    async def gen_first(self) -> {i}{base_name} | None:
        session = {session_getter_fn_name}()
        result = await session.execute(self.query.limit(1))
        return await self._gen_ent(result)

{gen_ent}

{gen_single_ent}

    async def genx_first(self) -> {i}{base_name}:
        ent = await self.gen_first()
        if not ent:
            raise EntNotFoundError(f"Expected query to return an ent, got None.")
        return ent

    async def gen_count_NO_PRIVACY(self) -> int:
        session = {session_getter_fn_name}()
        count_query = self.query.with_only_columns(func.count(), maintain_column_froms=True).order_by(None)
        result = await session.execute(count_query)
        count = result.scalar()
        if count is None:
            raise ExecutionError("Unable to get the count")
        return count

{order_by_methods}
""",
    )


def _generate_gen_ents(is_pattern: bool, base_name: str) -> str:
    i = "I" if is_pattern else ""
    if is_pattern:
        return f"""
    async def _gen_ents(self, result: Result[tuple[UUID]]) -> list[{i}{base_name} | None]:
        ent_ids = result.scalars().all()
        return [await self._gen_single_ent(ent_id) for ent_id in ent_ids]
"""  # noqa: E501
    return f"""
    async def _gen_ents(self, result: Result[tuple[{base_name}Model]]) -> list[{i}{base_name} | None]:
        models = result.scalars().all()
        return [await {base_name}._gen_from_model(self.vc, model) for model in models]
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
        return await {i}{base_name}._gen_from_model(self.vc, model)
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
        from .{to_snake_case(base_name)}_view import {base_name}View
        self.query = self.query.order_by({base_name}View.id.asc())
        return self

    def order_by_id_desc(self) -> "{i}{base_name}Query":
        from .{to_snake_case(base_name)}_view import {base_name}View
        self.query = self.query.order_by({base_name}View.id.desc())
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
