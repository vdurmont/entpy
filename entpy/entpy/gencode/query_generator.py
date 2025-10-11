from entpy import Schema
from entpy.gencode.generated_content import GeneratedContent


def generate(
    schema: Schema, base_name: str, session_getter_fn_name: str, vc_name: str
) -> GeneratedContent:
    return GeneratedContent(
        imports=[
            "from sqlalchemy.sql.expression import ColumnElement",
            "from typing import Any, TypeVar, Generic",
            "from sqlalchemy import select, Select, func",
        ],
        code=f"""
T = TypeVar("T")

class {base_name}Query(ABC, Generic[T]):
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


class {base_name}ListQuery({base_name}Query[{base_name}Model]):
    vc: {vc_name}

    def __init__(self, vc: {vc_name}) -> None:
        self.vc = vc
        self.query = select({base_name}Model)

    async def gen(self) -> list[{base_name}]:
        session = {session_getter_fn_name}()
        result = await session.execute(self.query)
        models = result.scalars().all()
        ents = [await {base_name}._gen_from_model(self.vc, model) for model in models]
        return list(filter(None, ents))

    async def gen_first(self) -> {base_name} | None:
        session = {session_getter_fn_name}()
        result = await session.execute(self.query.limit(1))
        model = result.scalar_one_or_none()
        return await {base_name}._gen_from_model(self.vc, model)

    async def genx_first(self) -> {base_name}:
        ent = await self.gen_first()
        if not ent:
            raise EntNotFoundError(f"Expected query to return an ent, got None.")
        return ent

class {base_name}CountQuery({base_name}Query[int]):
    def __init__(self) -> None:
        self.query = select(func.count()).select_from({base_name}Model)

    async def gen_NO_PRIVACY(self) -> int:
        session = {session_getter_fn_name}()
        result = await session.execute(self.query)
        count = result.scalar()
        if count is None:
            raise ExecutionError("Unable to get the count")
        return count
""",
    )
