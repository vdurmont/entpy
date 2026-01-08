import re
from dataclasses import dataclass

from entpy.framework.action import Action
from entpy.framework.descriptor import Descriptor


def to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def get_description(descriptor: Descriptor) -> str:
    content = descriptor.get_description()
    if content:
        return f'\n    """\n    {content}\n    """'
    return ""


@dataclass
class ImportedObject:
    module: str
    name: str

    def __str__(self) -> str:
        return f"from {self.module} import {self.name}"


@dataclass
class PrivacyRuleImport:
    rule: ImportedObject
    actions: list[Action]
