from sqlalchemy import (
    literal_column,
    select,
    union_all,
    Selectable,
)
from entpy.framework.view import create_view
from .ent_inherited_test import EntInheritedTestModel
from .ent_inherited_test_middle import EntInheritedTestMiddleModel

from database import Base


view_query: Selectable = union_all(
    select(
        literal_column("'EntInheritedTestModel'").label("ent_type"),
        EntInheritedTestModel.id,
        EntInheritedTestModel.created_at,
        EntInheritedTestModel.updated_at,
        EntInheritedTestModel.soft_deleted_at,
        EntInheritedTestModel.base_field,
        EntInheritedTestModel.middle_field,
    ),
)

ent_inherited_test_middle_view = create_view(
    "inherited_test_middle",
    view_query,
    metadata=Base.metadata,
    schema=None,
)
Base.registry.map_imperatively(
    EntInheritedTestMiddleModel, ent_inherited_test_middle_view
)
