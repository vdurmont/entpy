import re

from entpy.framework.descriptor import Descriptor


def to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def get_description(descriptor: Descriptor) -> str:
    content = descriptor.get_description()
    if content:
        return f'\n    """\n    {content}\n    """'
    return ""
