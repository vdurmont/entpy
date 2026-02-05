from entpy.framework.descriptor import Descriptor
from entpy.framework.pattern import Pattern
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import ImportedObject


def generate(
    descriptor: Descriptor,
    base_name: str,
    vc: ImportedObject,
    threshold_to_stop_loading_ents_for_count: int,
) -> GeneratedContent:
    is_pattern = isinstance(descriptor, Pattern)
    i = "I" if is_pattern else ""
    base_class = "EntPatternQuery" if is_pattern else "EntObjectQuery"

    return GeneratedContent(
        imports=[
            "from entpy.framework.query import " + base_class,
        ],
        code=f"""
class {i}{base_name}Query({base_class}[{vc.name}, {i}{base_name}, {base_name}Model]):
    ent_type = {i}{base_name}
    model_type = {base_name}Model
""",  # noqa: E501
    )
