from entpy import Schema
from entpy.gencode.generated_content import GeneratedContent


def generate(
    schema: Schema, base_name: str, session_getter_fn_name: str, vc_name: str
) -> GeneratedContent:
    return GeneratedContent(
        imports=[
            "from sqlalchemy.sql.expression import ColumnElement",
            "from typing import Any",
            "from sqlalchemy import select, Select",
        ],
        code=f"""
class {base_name}Query:
    vc: {vc_name}
    query: Select[tuple[{base_name}Model]]

    def __init__(self, vc: {vc_name}) -> None:
        self.vc = vc
        self.query = select({base_name}Model)

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

    async def gen(self) -> list[{base_name}]:
        session = {session_getter_fn_name}()
        result = await session.execute(self.query)
        models = result.scalars().all()
        ents = [await {base_name}._gen_from_model(self.vc, model) for model in models]
        return list(filter(None, ents))
""",
    )
