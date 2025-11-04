from sqlalchemy import literal_column, select, union_all, Table, Selectable
from sqlalchemy_utils import create_view
from .ent_test_thing import EntTestThingModel
from .ent_test_object2 import EntTestObject2Model
from .ent_test_object import EntTestObjectModel


view_query: Selectable = union_all(
    select(
        EntTestObjectModel.id,
        EntTestObjectModel.created_at,
        EntTestObjectModel.updated_at,
        EntTestObjectModel.a_good_thing,
        EntTestObjectModel.thing_status,
        literal_column("'EntTestObjectModel'").label("ent_type"),
    ),
    select(
        EntTestObject2Model.id,
        EntTestObject2Model.created_at,
        EntTestObject2Model.updated_at,
        EntTestObject2Model.a_good_thing,
        EntTestObject2Model.thing_status,
        literal_column("'EntTestObject2Model'").label("ent_type"),
    ),
)


class EntTestThingView:
    __table__: Table = create_view(
        name="ent_test_thing_view",
        selectable=view_query,
        metadata=EntTestThingModel.metadata,
        cascade_on_drop=None,
    )

    id = __table__.c.id
    created_at = __table__.c.created_at
    updated_at = __table__.c.updated_at
    ent_type = __table__.c.ent_type
    a_good_thing = __table__.c.a_good_thing
    thing_status = __table__.c.thing_status
