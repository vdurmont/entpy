from sqlalchemy import (
    literal_column,
    select,
    union_all,
    Selectable,
)
from entpy.framework.view import create_view
from .ent_test_object2 import EntTestObject2Model
from .ent_test_pattern import EntTestPatternModel

from database import Base


view_query: Selectable = union_all(
    select(
        literal_column("'EntTestObject2Model'").label("ent_type"),
        EntTestObject2Model.id,
        EntTestObject2Model.created_at,
        EntTestObject2Model.updated_at,
        EntTestObject2Model.soft_deleted_at,
        EntTestObject2Model.limit,
    ),
)

ent_test_pattern_view = create_view(
    "test_pattern",
    view_query,
    metadata=Base.metadata,
    schema=None,
)
Base.registry.map_imperatively(EntTestPatternModel, ent_test_pattern_view)
