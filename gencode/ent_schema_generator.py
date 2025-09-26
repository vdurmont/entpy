from dataclasses import dataclass
from pathlib import Path

from framework.ent_schema import EntSchema
from gencode.ent_base_generator import EntBaseGenerator
from gencode.ent_model_generator import EntModelGenerator


@dataclass
class Config:
    schema_class: type[EntSchema]
    output_path: Path


class EntSchemaGenerator:
    config: Config
    base_name: str
    ent_model_import: str

    def __init__(self, config: Config, ent_model_import: str):
        self.config = config
        self.base_name = self.config.schema_class.__name__.replace("Schema", "")
        self.ent_model_import = ent_model_import

    def generate(self) -> str:
        schema = self.config.schema_class()

        model_content = EntModelGenerator(
            schema=schema, base_name=self.base_name
        ).generate()
        base_content = EntBaseGenerator(base_name=self.base_name).generate()

        imports = [self.ent_model_import] + model_content.imports + base_content.imports
        imports = list(set(imports))  # Remove duplicates
        imports_code = "\n".join(imports)

        return f"""
{imports_code}

{model_content.code}

{base_content.code}
"""
