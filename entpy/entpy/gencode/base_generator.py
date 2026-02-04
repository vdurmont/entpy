from entpy import DateField, EdgeField, IntervalField, Schema, TimeField
from entpy.framework.descriptor import Descriptor
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
    vc: ImportedObject,
    prepended_rules: list[PrivacyRuleImport],
) -> GeneratedContent:
    extends = ",".join(
        [f"EntObjectBase[{vc.name}, {base_name}Model]"]
        + [
            f"I{pattern.__class__.__name__.removesuffix("Pattern")}"
            for pattern in schema.get_patterns()
        ]
    )

    fields = _generate_fields(schema)
    edge_gens, edge_types = _generate_edge_gens(schema)

    unique_gens = _generate_unique_gens(schema=schema, base_name=base_name, vc=vc)

    imports = [
        "from functools import cache",
        "from entpy import EdgeDelegate, PrivacyRule, Ent",
        "from entpy.framework.ent import EntObjectBase",
        "from entpy.framework.database import emulate_for_update",
    ]

    preprended_rules_str = ""
    for rule in prepended_rules:
        imports.append(str(rule.rule))
        actions = ", ".join([str(a) for a in rule.actions])
        preprended_rules_str += f"        if action in [{actions}]:\n"
        preprended_rules_str += (
            f"            prepended_rules.append({rule.rule.name}())\n"
        )

    imports += ["from sqlalchemy import select"]

    for pattern in schema.get_patterns():
        pattern_base_name = pattern.__class__.__name__.removesuffix("Pattern")
        class_name = f"I{pattern_base_name}"
        module_name = "." + to_snake_case(pattern_base_name)
        imports.append(f"from {module_name} import {class_name}")

    child_types = ""
    # Make the type checker happy for ents which implement multiple patterns
    if len(schema.get_patterns()) > 1:
        child_types = f"""@classmethod
    def _get_child_type(cls, uuid_type: bytes) -> type[{base_name}]:  # type: ignore[override]
        raise NotImplementedError("get_child_type() should only be called on patterns")
    """

    return GeneratedContent(
        imports=imports + fields.imports + edge_gens.imports,
        type_checking_imports=fields.type_checking_imports
        + edge_gens.type_checking_imports,
        code=f"""
class {base_name}({extends}):{get_description(schema)}
    m = {base_name}Model


    if TYPE_CHECKING:
{fields.code or "        pass"}

{unique_gens}

{edge_gens.code}

    @classmethod
    @cache
    def _get_edge_type(cls, edge_name: str) -> tuple[type[Ent], bool]:
{edge_types.code}
        return super()._get_edge_type(edge_name)

    async def _gen_evaluate_privacy(self, vc: {vc.name}, action: Action, default_to_deny: bool = True, log_on_deny: bool = True) -> Decision:
        # Build the complete list: prepended rules + entity's config
        prepended_rules: list[PrivacyRule] = []
{preprended_rules_str}
        config = {base_name}Schema().get_privacy_config(action)
        all_rules = prepended_rules + config

        # Evaluate each rule/delegate in order
        for item in all_rules:
            if isinstance(item, PrivacyRule):
                decision = await item.gen_evaluate_cached(vc, self)
                if decision == Decision.DENY and log_on_deny:
                    privacy_logger.debug("Privacy rule %s of {base_name} with ID %s was denied for %s", type(item), self.id, str(vc))
            elif isinstance(item, EdgeDelegate):
                edge_type = self._get_edge_type(item.edge_name)
                delegate = await edge_type[0]._genx_no_privacy_DO_NOT_USE(vc, getattr(self, f"{{item.edge_name}}_id"))
                decision = await delegate._gen_evaluate_privacy(vc, action, default_to_deny=False)
                if decision == Decision.DENY and log_on_deny:
                    privacy_logger.debug("Delegate privacy of {base_name} with ID %s to edge %s was denied for %s", self.id, item.edge_name, str(vc))
            else:
                raise ExecutionError("An invalid privacy configuration was found for {base_name}: invalid item type in list")
            # If we get an ALLOW or DENY, we return instantly. Else, we keep going.
            if decision != Decision.PASS:
                return decision
        # Return based on default behavior
        if default_to_deny:
            if log_on_deny:
                privacy_logger.debug("Defaulting to denying access to {base_name} with ID %s after exhausting all privacy rules for %s", self.id, str(vc))
            return Decision.DENY
        return Decision.PASS

    {child_types}

    @classmethod
    def query(cls, vc: {vc.name}) -> {base_name}Query:
        return {base_name}Query(vc=vc)
""",
    )


def _generate_fields(schema: Descriptor) -> GeneratedContent:
    fields = schema.get_all_fields()
    field_code = ""
    imports = ["from typing import Any, TYPE_CHECKING"]

    for field in fields:
        if isinstance(field, DateField):
            imports.append("from datetime import date")
        if isinstance(field, TimeField):
            imports.append("from datetime import time")
        if isinstance(field, IntervalField):
            imports.append("from datetime import timedelta")
        accessor_type = field.get_python_type() + (" | None" if field.nullable else "")
        field_code += f"        {field.name}: {accessor_type}\n"
        if field.description:
            field_code += f"""        \"\"\"
        {field.description}
        \"\"\"\n"""

    return GeneratedContent(
        imports=imports,
        code=field_code,
    )


def _generate_edge_gens(
    schema: Descriptor,
) -> tuple[GeneratedContent, GeneratedContent]:
    fields = schema.get_sorted_fields()
    type_stubs = ""
    edge_types = ""
    type_checking_imports = []

    for field in fields:
        # If the field is an edge, we want to generate a utility function to
        # load the edge directly
        if isinstance(field, EdgeField):
            load = ""
            if field.edge_class != schema.__class__:
                module = "." + to_snake_case(
                    field.edge_class.__name__.removesuffix("Schema").removesuffix(
                        "Pattern"
                    )
                )
                # We import the edge type locally to avoid circular imports
                type_checking_imports.append(
                    f"from {module} import {field.get_edge_type()}"
                )
                load = f"from {module} import {field.get_edge_type()}\n        "
            type_stubs += f"""
        async def gen_{field.original_name}(self) -> "{field.get_edge_type()}"{" | None" if field.nullable else ""}:
            pass

"""  # noqa: E501

            edge_types += f'            case "{field.original_name}":\n'
            edge_types += f"                {load}\n"
            edge_types += (
                f"                return ({field.get_edge_type()}, {field.nullable})\n"
            )

    return (
        GeneratedContent(
            type_checking_imports=type_checking_imports,
            code=type_stubs,
        ),
        GeneratedContent(
            code=f"        match edge_name:\n{edge_types}" if edge_types else "",
        ),
    )


def _generate_unique_gens(
    schema: Descriptor, base_name: str, vc: ImportedObject
) -> str:
    unique_gens = ""
    for field in schema.get_sorted_fields():
        if field.is_unique:
            unique_gens += f"""
        @classmethod
        async def gen_from_{field.name}(cls, vc: {vc.name}, {field.name}: {field.get_python_type()}, for_update: bool = False) -> Self | None:
            pass

        @classmethod
        async def genx_from_{field.name}(cls, vc: {vc.name}, {field.name}: {field.get_python_type()}, for_update: bool = False) -> Self:
            pass
"""  # noqa: E501
    return unique_gens
