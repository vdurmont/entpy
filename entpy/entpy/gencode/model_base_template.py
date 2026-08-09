def generate(base_import: str) -> str:
    return f"""from entpy.framework.model import ModelMixin

{base_import}

class EntModel(Base, ModelMixin):
    __abstract__ = True
"""
