from entpy import DateField, EdgeField, IntervalField, Schema, TimeField
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import (
    ImportedObject,
    PrivacyRuleImport,
    get_description,
    to_snake_case,
)


def generate(
    schema: Schema,
    base_name: str,
    session_getter: ImportedObject,
    vc: ImportedObject,
    prepended_rules: list[PrivacyRuleImport],
) -> GeneratedContent:
    extends = ",".join(
        [
            f"I{pattern.__class__.__name__.replace("Pattern", "")}"
            for pattern in schema.get_patterns()
        ]
        + [f"Ent[{vc.name}]"]
    )

    accessors = _generate_accessors(schema)

    unique_gens = _generate_unique_gens(schema=schema, base_name=base_name, vc=vc)

    imports = [
        "from entpy import EdgeDelegate, PrivacyRule, Ent",
        "from entpy.framework.database import emulate_for_update",
    ]

    preprended_rules_str = ""
    # Iterating in reverse because we insert each one at index 0 and want to
    # keep the user's rules order
    for rule in reversed(prepended_rules):
        imports.append(str(rule.rule))
        actions = ", ".join([str(a) for a in rule.actions])
        preprended_rules_str += f"            if action in [{actions}]:\n"
        preprended_rules_str += (
            f"                config.insert(0, {rule.rule.name}())\n"
        )

    imports += ["from sqlalchemy import select"]

    for pattern in schema.get_patterns():
        pattern_base_name = pattern.__class__.__name__.replace("Pattern", "")
        class_name = f"I{pattern_base_name}"
        module_name = "." + to_snake_case(pattern_base_name)
        imports.append(f"from {module_name} import {class_name}")

    delegate_loaders = ""
    for field in schema.get_all_fields():
        if isinstance(field, EdgeField) and not field.nullable:
            other_ent = field.get_edge_type()
            other_module = to_snake_case(other_ent).replace("i_", "")
            delegate_loaders += f"""
        if edge_name == "{field.original_name}":
            from .{other_module} import {other_ent}
            return await {other_ent}._genx_no_privacy_DO_NOT_USE(vc, self.{field.name})
"""

    return GeneratedContent(
        imports=imports + accessors.imports,
        type_checking_imports=accessors.type_checking_imports,
        code=f"""
class {base_name}({extends}):{get_description(schema)}
    vc: {vc.name}
    model: {base_name}Model

    def __init__(self, vc: {vc.name}, model: {base_name}Model) -> None:
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

    @property
    def soft_deleted_at(self) -> datetime | None:
        return self.model.soft_deleted_at

{accessors.code}

    async def _gen_evaluate_privacy(self, vc: {vc.name}, action: Action) -> Decision:
        config = {base_name}Schema().get_privacy_config(action)
        if isinstance(config, EdgeDelegate):
            delegate = await self._gen_load_delegate(vc, config.edge_name)
            decision = await delegate._gen_evaluate_privacy(vc, action)
            if decision == Decision.DENY:
                privacy_logger.debug("Delegate privacy of {base_name} with ID %s to edge %s was denied for %s", self.id, config.edge_name, str(vc))
            return decision
        elif isinstance(config, list) and all(isinstance(item, PrivacyRule) for item in config):
{preprended_rules_str}
            session = {session_getter.name}()
            for rule in config:
                decision = await rule.gen_evaluate_cached(session, vc, self)
                if decision == Decision.DENY:
                    privacy_logger.debug("Privacy rule %s of {base_name} with ID %s was denied for %s", type(rule), self.id, str(vc))
                # If we get an ALLOW or DENY, we return instantly. Else, we keep going.
                if decision != Decision.PASS:
                    return decision
            # We default to denying
            privacy_logger.debug("Defaulting to denying access to {base_name} with ID %s after exhausting all privacy rules for %s", self.id, str(vc))
            return Decision.DENY
        raise ExecutionError("An invalid privacy configuration was found for {base_name}: invalid config type")

    async def _gen_load_delegate(self, vc: {vc.name}, edge_name: str) -> Ent:{delegate_loaders}
        raise ExecutionError(f"An invalid privacy configuration was found for {base_name}: could not find delegate for {{edge_name}}")

    @classmethod
    async def _gen_no_privacy_DO_NOT_USE(cls, vc: {vc.name}, ent_id: UUID | str, for_update: bool = False) -> {base_name} | None:
        real_ent_id = validate_ent_id(ent_id)
        session = {session_getter.name}()
        model = await session.get({base_name}Model, real_ent_id, with_for_update=for_update or None)
        if model is None:
            return None
        return {base_name}(vc=vc, model=model)

    @classmethod
    async def _genx_no_privacy_DO_NOT_USE(cls, vc: {vc.name}, ent_id: UUID | str, for_update: bool = False) -> {base_name}:
        ent = await {base_name}._gen_no_privacy_DO_NOT_USE(vc, ent_id, for_update)
        if ent is None:
            raise EntNotFoundError(f"No {base_name} found for ID {{ent_id}}")
        return ent

    @classmethod
    async def genx(
        cls, vc: {vc.name}, ent_id: UUID | str, for_update: bool = False
    ) -> {base_name}:
        ent = await cls.gen(vc, ent_id, for_update)
        if not ent:
            raise EntNotFoundError(f"No {base_name} found for ID {{ent_id}}")
        return ent

    @classmethod
    async def gen(
        cls, vc: {vc.name}, ent_id: UUID | str, for_update: bool = False
    ) -> {base_name} | None:
        real_ent_id = validate_ent_id(ent_id)
        session = {session_getter.name}()
        async with emulate_for_update(session, {base_name}Model, "id", real_ent_id, for_update):
            model = await session.get({base_name}Model, real_ent_id, with_for_update=for_update or None)
        session.info.setdefault("cache", set()).add(model)
        return await cls._gen_from_model(vc, model)  # noqa: SLF001

    {unique_gens}

    @classmethod
    async def _gen_from_model(
        cls, vc: {vc.name}, model: {base_name}Model | None
    ) -> {base_name} | None:
        if not model:
            return None
        ent = {base_name}(vc=vc, model=model)
        decision = await ent._gen_evaluate_privacy(vc=vc, action=Action.READ)
        return ent if decision == Decision.ALLOW else None

    @classmethod
    async def _genx_from_model(
        cls, vc: {vc.name}, model: {base_name}Model
    ) -> {base_name}:
        ent = await {base_name}._gen_from_model(vc=vc, model=model)
        if not ent:
            raise EntNotFoundError(f"No {base_name} found for ID {{model.id}}")
        return ent

    @classmethod
    def query(cls, vc: {vc.name}) -> {base_name}Query:
        return {base_name}Query(vc=vc)
""",
    )


def _generate_accessors(schema: Schema) -> GeneratedContent:
    fields = schema.get_all_fields()
    accessors_code = ""
    imports = []
    type_checking_imports = []

    for field in fields:
        if isinstance(field, DateField):
            imports.append("from datetime import date")
        if isinstance(field, TimeField):
            imports.append("from datetime import time")
        if isinstance(field, IntervalField):
            imports.append("from datetime import timedelta")
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
            load = ""
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
                load = f"from {module} import {field.get_edge_type()}\n        "
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
        imports=imports,
        type_checking_imports=type_checking_imports,
        code=accessors_code,
    )


def _generate_unique_gens(schema: Schema, base_name: str, vc: ImportedObject) -> str:
    unique_gens = ""
    for field in schema.get_all_fields():
        if field.is_unique:
            unique_gens += f"""
    @classmethod
    async def gen_from_{field.name}(cls, vc: {vc.name}, {field.name}: {field.get_python_type()}, for_update: bool = False) -> {base_name} | None:
        session = get_session()
        query = select({base_name}Model).where({base_name}Model.{field.name} == {field.name})
        query = query.with_for_update()
        async with emulate_for_update(session, {base_name}Model, "{field.name}", {field.name}, for_update):
            result = await session.execute(query)
        model = result.scalar_one_or_none()
        session.info.setdefault("cache", set()).add(model)
        return await cls._gen_from_model(vc, model)  # noqa: SLF001

    @classmethod
    async def genx_from_{field.name}(cls, vc: {vc.name}, {field.name}: {field.get_python_type()}, for_update: bool = False) -> {base_name}:
        result = await cls.gen_from_{field.name}(vc, {field.name}, for_update)
        if not result:
            raise EntNotFoundError(f"No EntTestObject found for {field.name} {{{field.name}}}")
        return result
"""  # noqa: E501
    return unique_gens
