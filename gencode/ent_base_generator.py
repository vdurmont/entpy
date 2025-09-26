from gencode.generated_content import GeneratedContent


def generate(base_name: str) -> GeneratedContent:
    return GeneratedContent(
        imports=[
            "from framework.viewer_context import ViewerContext",
            "from uuid import UUID",
        ],
        code=f"""
class {base_name}:
    vc: ViewerContext
    model: {base_name}Model

    def __init__(self, vc: ViewerContext, model: {base_name}Model) -> None:
        self.vc = vc
        self.model = model

    @staticmethod
    def gen_nullable(vc: ViewerContext, id: UUID) -> "{base_name}" | None:
        return None
""",
    )
