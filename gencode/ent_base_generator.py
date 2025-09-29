from framework.ent_schema import EntSchema
from gencode.generated_content import GeneratedContent


def generate(
    schema: EntSchema, base_name: str, session_getter_import: str
) -> GeneratedContent:
    accessors = _generate_accessors(schema)

    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
            "from uuid import UUID",
        ]
        + [session_getter_import],
        code=f"""
class {base_name}:
    vc: ViewerContext
    model: {base_name}Model

    def __init__(self, vc: ViewerContext, model: {base_name}Model) -> None:
        self.vc = vc
        self.model = model

{accessors}

    @classmethod
    async def gen_nullable(
        cls, vc: ViewerContext, ent_id: UUID
    ) -> {base_name} | None:
        async for session in get_session():
            model = await session.get({base_name}Model, ent_id)
            return await cls._gen_nullable_from_model(vc, model)

    @classmethod
    async def _gen_nullable_from_model(
        cls, vc: ViewerContext, model: {base_name}Model | None
    ) -> {base_name} | None:
        if not model:
            return None
        ent = {base_name}(vc=vc, model=model)
        # TODO check privacy here
        return ent
""",
    )


def _generate_accessors(schema: EntSchema) -> str:
    fields = schema.get_fields()
    accessors_code = ""
    for field in fields:
        accessors_code += f"""    @property
    def {field.name}(self) -> {field.get_python_type()}:
        return self.model.{field.name}

"""
    return accessors_code
