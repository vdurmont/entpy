from sqlalchemy import (
    DDL,
    Column,
    MetaData,
    Table,
    event,
    literal_column,
    select,
    union_all,
    Selectable,
)
from .ent_test_thing import EntTestThingModel
from sqlalchemy import String
from .ent_test_object import EntTestObjectModel
from sqlalchemy import Enum as DBEnum
from ent_test_thing_pattern import ThingStatus
from sqlalchemy.dialects.postgresql import UUID as DBUUID
from sqlalchemy import DateTime
from .ent_test_object2 import EntTestObject2Model


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


# Compile the view query to SQL
view_sql = str(view_query.compile(compile_kwargs={"literal_binds": True})).replace(
    "\n", " "
)

# Create the view DDL with IF NOT EXISTS for idempotency
create_view_ddl = DDL(f"CREATE VIEW IF NOT EXISTS ent_test_thing_view AS {view_sql}")

# Create the drop view DDL with IF EXISTS for idempotency
drop_view_ddl = DDL("DROP VIEW IF EXISTS ent_test_thing_view")


# Create a separate metadata for the view table so it's not
# processed by create_all/drop_all
# This prevents SQLAlchemy from trying to CREATE TABLE for the view
_view_metadata = MetaData()

_view_table = Table(
    "ent_test_thing_view",
    _view_metadata,
    Column("id", DBUUID(as_uuid=True), primary_key=True),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
    Column("ent_type", String(50)),
    Column("a_good_thing", String(100), nullable=False),
    Column("thing_status", DBEnum(ThingStatus, native_enum=True), nullable=True),
    info={"is_view": True},
)


class EntTestThingView:
    __table__ = _view_table

    id = __table__.c.id
    created_at = __table__.c.created_at
    updated_at = __table__.c.updated_at
    ent_type = __table__.c.ent_type
    a_good_thing = __table__.c.a_good_thing
    thing_status = __table__.c.thing_status


# Register DDL events to create/drop the view on the main metadata
event.listen(
    EntTestThingModel.metadata,
    "after_create",
    create_view_ddl.execute_if(dialect="sqlite"),
)
event.listen(
    EntTestThingModel.metadata,
    "after_create",
    create_view_ddl.execute_if(dialect="postgresql"),
)

event.listen(
    EntTestThingModel.metadata,
    "before_drop",
    drop_view_ddl.execute_if(dialect="sqlite"),
)
event.listen(
    EntTestThingModel.metadata,
    "before_drop",
    drop_view_ddl.execute_if(dialect="postgresql"),
)
