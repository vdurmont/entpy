from gencode.generated_content import GeneratedContent


class EntModelGenerator:
    base_name: str

    def __init__(self, base_name: str):
        self.base_name = base_name

    def generate(self) -> GeneratedContent:
        return GeneratedContent(
            code=f"""
class {self.base_name}Model:
    pass
"""
        )
