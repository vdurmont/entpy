from entpy import EdgeField, Schema
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


def generate(
    schema: Schema,
    base_name: str,
    session_getter_fn_name: str,
) -> GeneratedContent:
    extends = ",".join(
        ["Ent"]
        + [
            f"I{pattern.__class__.__name__.replace("Pattern", "")}"
            for pattern in schema.get_patterns()
        ]
    )

    accessors = _generate_accessors(schema)

    unique_gens = _generate_unique_gens(schema=schema, base_name=base_name)

    imports = []

    if unique_gens:
        # only add this import if we have unique gens :)
        imports += ["from sqlalchemy import select"]

    for pattern in schema.get_patterns():
        pattern_base_name = pattern.__class__.__name__.replace("Pattern", "")
        class_name = f"I{pattern_base_name}"
        module_name = "." + to_snake_case(pattern_base_name)
        imports.append(f"from {module_name} import {class_name}")

    return GeneratedContent(
        imports=imports,
        code=f"""
class {base_name}({extends}):
    vc: ViewerContext
    model: {base_name}Model

    def __init__(self, vc: ViewerContext, model: {base_name}Model) -> None:
        self.vc = vc
        self.model = model

    @property
    def id(self) -> UUID:
        return self.model.id

    @property
    def created_at(self) -> datetime:
        return self.model.created_at

    @property
    def updated_at(self) -> datetime:
        return self.model.updated_at

{accessors}

    @classmethod
    async def genx(
        cls, vc: ViewerContext, ent_id: UUID
    ) -> {base_name}:
        ent = await cls.gen(vc, ent_id)
        if not ent:
            raise ValueError(f"No {base_name} found for ID {{ent_id}}")
        return ent

    @classmethod
    async def gen(
        cls, vc: ViewerContext, ent_id: UUID
    ) -> {base_name} | None:
        session = {session_getter_fn_name}()
        model = await session.get({base_name}Model, ent_id)
        return await cls._gen_from_model(vc, model)

    {unique_gens}

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
    fields = schema.get_all_fields()
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


def _generate_unique_gens(schema: Schema, base_name: str) -> str:
    unique_gens = ""
    for field in schema.get_all_fields():
        if field.is_unique:
            unique_gens += f"""
    @classmethod
    async def gen_from_{field.name}(cls, vc: ViewerContext, {field.name}: {field.get_python_type()}) -> {base_name} | None:
        session = get_session()
        result = await session.execute(
            select({base_name}Model)
            .where({base_name}Model.{field.name} == {field.name})
        )
        model = result.scalar_one_or_none()
        return await cls._gen_from_model(vc, model)

    @classmethod
    async def genx_from_{field.name}(cls, vc: ViewerContext, {field.name}: {field.get_python_type()}) -> {base_name}:
        result = await cls.gen_from_{field.name}(vc, {field.name})
        if not result:
            raise ValueError(f"No EntTestObject found for {field.name} {{{field.name}}}")
        return result
"""
    return unique_gens
