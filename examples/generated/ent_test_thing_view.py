from sqlalchemy import (
    Table,
    literal_column,
    select,
    union_all,
    Selectable,
)
from entpy.framework.view import create_view
from .ent_test_object import EntTestObjectModel
from .ent_test_object2 import EntTestObject2Model

from database import Base


view_query: Selectable = union_all(
    select(
        literal_column("'EntTestObject2Model'").label("ent_type"),
        EntTestObject2Model.id,
        EntTestObject2Model.created_at,
        EntTestObject2Model.updated_at,
        EntTestObject2Model.soft_deleted_at,
        EntTestObject2Model.a_good_thing,
        EntTestObject2Model.obj5_id,
        EntTestObject2Model.a_pattern_validated_field,
        EntTestObject2Model.obj5_opt_id,
        EntTestObject2Model.thing_status,
    ),
    select(
        literal_column("'EntTestObjectModel'").label("ent_type"),
        EntTestObjectModel.id,
        EntTestObjectModel.created_at,
        EntTestObjectModel.updated_at,
        EntTestObjectModel.soft_deleted_at,
        EntTestObjectModel.a_good_thing,
        EntTestObjectModel.obj5_id,
        EntTestObjectModel.a_pattern_validated_field,
        EntTestObjectModel.obj5_opt_id,
        EntTestObjectModel.thing_status,
    ),
)


class EntTestThingView(Base):
    __table__: Table = create_view(
        "ent_test_thing_view",
        view_query,
        metadata=Base.metadata,
    )
