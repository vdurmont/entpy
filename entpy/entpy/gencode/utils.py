import re

from entpy.framework.descriptor import Descriptor
from entpy.framework.fields.core import Field


def to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def get_description(descriptor: Descriptor) -> str:
    content = descriptor.get_description()
    if content:
        return f'\n    """\n    {content}\n    """'
    return ""


def get_field(descriptor: Descriptor, field_name: str) -> Field:
    for field in descriptor.get_all_fields():
        if field.name == field_name:
            return field
    raise ValueError(f"Unknown field {field_name} in {descriptor.__class__.__name__}")
