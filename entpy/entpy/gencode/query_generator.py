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
    ]

    if is_pattern:
        imports.append("from typing import cast")

    # For patterns, we need to import and use the view
    query_target = f"{base_name}View.__table__" if is_pattern else f"{base_name}Model"
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
    generic = "UUID" if is_pattern else f"{base_name}Model"

    return GeneratedContent(
        imports=imports,
        code=f"""
T = TypeVar("T")

class {i}{base_name}Query(ABC, Generic[T]):
    query: Select[tuple[T]]

    def join(self, model_class: type[EntModel], predicate: ColumnElement[bool]) -> Self:
        self.query = self.query.join(model_class, predicate)
        return self

    def where(self, predicate: ColumnElement[bool]) -> Self:
        self.query = self.query.where(predicate)
        return self

    def order_by(self, predicate: ColumnElement[Any]) -> Self:
        self.query = self.query.order_by(predicate)
        return self

    def limit(self, limit: int) -> Self:
        self.query = self.query.limit(limit)
        return self


class {i}{base_name}ListQuery({i}{base_name}Query[{generic}]):
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

class {i}{base_name}CountQuery({i}{base_name}Query[int]):
    def __init__(self) -> None:
        {view_import}
        self.query = select(func.count()).select_from({query_target})

    async def gen_NO_PRIVACY(self) -> int:
        session = {session_getter_fn_name}()
        result = await session.execute(self.query)
        count = result.scalar()
        if count is None:
            raise ExecutionError("Unable to get the count")
        return count
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
