from framework.fields.edge_field import EdgeField
from framework.schema import Schema
from gencode.generated_content import GeneratedContent


def generate(
    schema: Schema,
    base_name: str,
    session_getter_fn_name: str,
) -> GeneratedContent:
    accessors = _generate_accessors(schema)

    return GeneratedContent(
        imports=[],
        code=f"""
class {base_name}:
    vc: ViewerContext
    model: {base_name}Model

    def __init__(self, vc: ViewerContext, model: {base_name}Model) -> None:
        self.vc = vc
        self.model = model

    @property
    def id(self) -> UUID:
        return self.model.id

{accessors}

    @classmethod
    async def genx(
        cls, vc: ViewerContext, ent_id: UUID
    ) -> {base_name}:
        ent = await cls.gen(vc, ent_id)
        if not ent:
            raise ValueError("No {{base_name}} found for ID {{ent_id}}")
        return ent

    @classmethod
    async def gen(
        cls, vc: ViewerContext, ent_id: UUID
    ) -> {base_name} | None:
        session = {session_getter_fn_name}()
        model = await session.get({base_name}Model, ent_id)
        return await cls._gen_from_model(vc, model)

    @classmethod
    async def _gen_from_model(
        cls, vc: ViewerContext, model: {base_name}Model | None
    ) -> {base_name} | None:
        if not model:
            return None
        ent = {base_name}(vc=vc, model=model)
        # TODO check privacy here
        return ent

    @classmethod
    async def _genx_from_model(
        cls, vc: ViewerContext, model: {base_name}Model
    ) -> {base_name}:
        ent = {base_name}(vc=vc, model=model)
        # TODO check privacy here
        return ent
""",
    )


def _generate_accessors(schema: Schema) -> str:
    fields = schema.get_sorted_fields()
    accessors_code = ""
    for field in fields:
        accessor_type = field.get_python_type() + (" | None" if field.nullable else "")
        accessors_code += f"""    @property
    def {field.name}(self) -> {accessor_type}:
        return self.model.{field.name}

"""

        # If the field is an edge, we want to generate a utility function to
        # load the edge directly
        if isinstance(field, EdgeField):
            if field.nullable:
                accessors_code += f"""
    async def gen_{field.original_name}(self) -> {field.get_edge_type()} | None:
        if self.model.{field.name}:
            return await {field.get_edge_type()}.gen(self.vc, self.model.{field.name})
        return None

"""  # noqa: E501
            else:
                accessors_code += f"""
    async def gen_{field.original_name}(self) -> {field.get_edge_type()}:
        return await {field.get_edge_type()}.genx(self.vc, self.model.{field.name})

"""  # noqa: E501
    return accessors_code
