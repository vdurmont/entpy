from gencode.generated_content import GeneratedContent


class EntBaseGenerator:
    base_name: str

    def __init__(self, base_name: str):
        self.base_name = base_name

    def generate(self) -> GeneratedContent:
        return GeneratedContent(
            imports=[
                "from framework.viewer_context import ViewerContext",
                "from uuid import UUID",
            ],
            code=f"""
class {self.base_name}:
    vc: ViewerContext
    model: {self.base_name}Model

    def __init__(self, vc: ViewerContext, model: {self.base_name}Model) -> None:
        self.vc = vc
        self.model = model

    @staticmethod
    def gen_nullable(vc: ViewerContext, id: UUID) -> "{self.base_name}" | None:
        return None
""",
        )
