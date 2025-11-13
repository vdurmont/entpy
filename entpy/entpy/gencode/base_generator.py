from entpy import EdgeField, EnumField, ExpandedEdge, Schema
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import get_description, get_field, to_snake_case


def generate(
    schema: Schema, base_name: str, session_getter_fn_name: str, vc_name: str
) -> GeneratedContent:
    extends = ",".join(
        [
            f"I{pattern.__class__.__name__.replace("Pattern", "")}"
            for pattern in schema.get_patterns()
        ]
        + [f"Ent[{vc_name}]"]
    )

    accessors = _generate_accessors(schema)

    unique_gens = _generate_unique_gens(
        schema=schema, base_name=base_name, vc_name=vc_name
    )

    imports = []

    if unique_gens:
        # only add this import if we have unique gens :)
        imports += ["from sqlalchemy import select"]

    for pattern in schema.get_patterns():
        pattern_base_name = pattern.__class__.__name__.replace("Pattern", "")
        class_name = f"I{pattern_base_name}"
        module_name = "." + to_snake_case(pattern_base_name)
        imports.append(f"from {module_name} import {class_name}")

    to_json = _generate_to_json(schema=schema, base_name=base_name)

    return GeneratedContent(
        imports=imports + accessors.imports + to_json.imports,
        type_checking_imports=accessors.type_checking_imports,
        code=f"""
class {base_name}({extends}):{get_description(schema)}
    vc: {vc_name}
    model: {base_name}Model

    def __init__(self, vc: {vc_name}, model: {base_name}Model) -> None:
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

{accessors.code}

    async def _gen_evaluate_privacy(self, vc: {vc_name}, action: Action) -> Decision:
        rules = {base_name}Schema().get_privacy_rules(action)
        for rule in rules:
            decision = await rule.gen_evaluate(vc, self)
            # If we get an ALLOW or DENY, we return instantly. Else, we keep going.
            if decision != Decision.PASS:
                return decision
        # We default to denying
        return Decision.DENY

    @classmethod
    async def genx(
        cls, vc: {vc_name}, ent_id: UUID | str
    ) -> {base_name}:
        ent = await cls.gen(vc, ent_id)
        if not ent:
            raise EntNotFoundError(f"No {base_name} found for ID {{ent_id}}")
        return ent

    @classmethod
    async def gen(
        cls, vc: {vc_name}, ent_id: UUID | str
    ) -> {base_name} | None:
        # Convert str to UUID if needed
        if isinstance(ent_id, str):
            try:
                ent_id = UUID(ent_id)
            except ValueError as e:
                raise ValidationError(f"Invalid ID format for {{ent_id}}") from e

        session = {session_getter_fn_name}()
        model = await session.get({base_name}Model, ent_id)
        return await cls._gen_from_model(vc, model)

    {unique_gens}

    @classmethod
    async def _gen_from_model(
        cls, vc: {vc_name}, model: {base_name}Model | None
    ) -> {base_name} | None:
        if not model:
            return None
        ent = {base_name}(vc=vc, model=model)
        decision = await ent._gen_evaluate_privacy(vc=vc, action=Action.READ)
        return ent if decision == Decision.ALLOW else None

    @classmethod
    async def _genx_from_model(
        cls, vc: {vc_name}, model: {base_name}Model
    ) -> {base_name}:
        ent = await {base_name}._gen_from_model(vc=vc, model=model)
        if not ent:
            raise EntNotFoundError(f"No {base_name} found for ID {{model.id}}")
        return ent

    @classmethod
    def query(cls, vc: {vc_name}) -> {base_name}ListQuery:
        return {base_name}ListQuery(vc=vc)

    @classmethod
    def query_count(cls, vc: {vc_name}) -> {base_name}CountQuery:
        return {base_name}CountQuery()

{to_json.code}
""",
    )


def _generate_accessors(schema: Schema) -> GeneratedContent:
    fields = schema.get_all_fields()
    accessors_code = ""
    type_checking_imports = []
    for field in fields:
        accessor_type = field.get_python_type() + (" | None" if field.nullable else "")
        description = field.description
        if description:
            description = f"""\"\"\"
        {description}
        \"\"\"
        """
        accessors_code += f"""    @property
    def {field.name}(self) -> {accessor_type}:
        {description if description else ""}return self.model.{field.name}

"""

        # If the field is an edge, we want to generate a utility function to
        # load the edge directly
        if isinstance(field, EdgeField):
            if field.edge_class != schema.__class__:
                module = "." + to_snake_case(
                    field.edge_class.__name__.replace("Schema", "").replace(
                        "Pattern", ""
                    )
                )
                # We import the edge type locally to avoid circular imports
                type_checking_imports.append(
                    f"from {module} import {field.get_edge_type()}"
                )
                load = (
                    f"from {module} import {field.get_edge_type()}\n        "
                    if field.edge_class != schema.__class__
                    else ""
                )
            if field.nullable:
                accessors_code += f"""
    async def gen_{field.original_name}(self) -> "{field.get_edge_type()}" | None:
        {load}if self.model.{field.name}:
            return await {field.get_edge_type()}.gen(self.vc, self.model.{field.name})
        return None

"""  # noqa: E501
            else:
                accessors_code += f"""
    async def gen_{field.original_name}(self) -> {field.get_edge_type()}:
        {load}return await {field.get_edge_type()}.genx(self.vc, self.model.{field.name})

"""  # noqa: E501
    return GeneratedContent(
        type_checking_imports=type_checking_imports, code=accessors_code
    )


def _generate_unique_gens(schema: Schema, base_name: str, vc_name: str) -> str:
    unique_gens = ""
    for field in schema.get_all_fields():
        if field.is_unique:
            unique_gens += f"""
    @classmethod
    async def gen_from_{field.name}(cls, vc: {vc_name}, {field.name}: {field.get_python_type()}) -> {base_name} | None:
        session = get_session()
        result = await session.execute(
            select({base_name}Model)
            .where({base_name}Model.{field.name} == {field.name})
        )
        model = result.scalar_one_or_none()
        return await cls._gen_from_model(vc, model)

    @classmethod
    async def genx_from_{field.name}(cls, vc: {vc_name}, {field.name}: {field.get_python_type()}) -> {base_name}:
        result = await cls.gen_from_{field.name}(vc, {field.name})
        if not result:
            raise EntNotFoundError(f"No EntTestObject found for {field.name} {{{field.name}}}")
        return result
"""  # noqa: E501
    return unique_gens


def _generate_to_json(schema: Schema, base_name: str) -> GeneratedContent:
    base_fields = ""
    for field in schema.get_all_fields():
        if isinstance(field, EnumField):
            base_fields += f"""
            "{field.name}": self.{field.name}.name if self.{field.name} else None,"""
        elif isinstance(field, EdgeField):
            base_fields += f"""
            "{field.name}": str(self.{field.name}) if self.{field.name} else None,"""
        else:
            base_fields += f"""
            "{field.name}": self.{field.name},"""

    edges_fields = ""
    for field in schema.get_all_fields():
        if isinstance(field, EdgeField):
            edges_fields += f"""
        if field_name == "{field.original_name}":
            return await self.gen_{field.original_name}()
"""

    groups: dict[str, list[str]] = {}
    for field in schema.get_all_fields():
        for g in field.json_groups:
            g_name = g if isinstance(g, str) else g.group_name
            if g_name in groups:
                groups[g_name].append(field.name)
            else:
                groups[g_name] = [field.name]
    groups_code = ""
    for group_name, group_value in groups.items():
        group_items = ['"id"', '"created_at"', '"updated_at"']
        for item in group_value:
            field = get_field(schema, item)
            if isinstance(field.json_groups[group_name], str):
                group_items.append(f'"{field.original_name}"')
            else:
                group_items.append(_render_expanded_edge(field.json_groups[group_name]))
        groups_code += f'        "{group_name}": [{", ".join(group_items)}],'

    return GeneratedContent(
        imports=["from entpy import ExpandedEdge, EdgeField", "from typing import Any"],
        code=f"""
    json_groups: dict[str, list[str | ExpandedEdge]] = {{
{groups_code}
    }}

    async def to_json(
        self,
        fields: list[str | ExpandedEdge] | None = None,
        group: str | None = None,
    ) -> dict[str, Any]:
        if fields and group:
            raise ExecutionError(
                "Cannot use both `fields` and `group` in the `to_json` function."
                + " Pick one."
            )
        base_fields = {{
            "id": str(self.id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
{base_fields}
        }}
        if not fields and not group:
            return base_fields

        if group:
            fields = self.json_groups[group] if group in self.json_groups else ["id", "created_at", "updated_at"]

        if not fields:
            fields = ["id", "created_at", "updated_at"]

        result: dict[str, Any] = {{}}
        for field in fields:
            if isinstance(field, str):
                if field in ["id", "created_at", "updated_at"]:
                    field_name = field
                else:
                    f = _get_field(field)
                    field_name = (
                        f"{{field}}_id" if isinstance(f, EdgeField) else field
                    )
                result[field_name] = base_fields[field_name]
            else:
                edge = await self._gen_edge(field.edge_name)
                edge_json = (
                    await edge.to_json(fields=field.fields, group=field.group)
                    if edge
                    else None
                )
                result[field.edge_name] = edge_json

        return result

    async def _gen_edge(self, field_name: str) -> Ent | None:
{edges_fields}
        raise ExecutionError(f"Trying to fetch unknown edge: {{field_name}}")
""",  # noqa: E501
    )


def _render_expanded_edge(edge: ExpandedEdge) -> str:
    # Convert the groups to a string
    groups = "[" if edge.groups else "None"
    for g in edge.groups or []:
        groups += f'"{g}", '
    if edge.groups:
        groups += "]"

    # Convert the fields to a string
    fields = "[" if edge.fields else "None"
    for f in edge.fields or []:
        if isinstance(f, str):
            fields += f'"{f}", '
        else:
            fields += _render_expanded_edge(f) + ", "
    if edge.fields:
        fields += "]"

    return f"""ExpandedEdge(
    edge_name="{edge.edge_name}",
    fields={fields},
    group={f"\"{edge.group}\"" if edge.group else "None"},
    groups={groups},
)"""
