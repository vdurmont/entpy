from entpy import Ent
from evc import ExampleViewerContext

from .ent_child import EntChildModel  # noqa: F401
from .ent_child import EntChild
from .ent_grand_parent import EntGrandParentModel  # noqa: F401
from .ent_grand_parent import EntGrandParent
from .ent_parent import EntParentModel  # noqa: F401
from .ent_parent import EntParent
from .ent_test_object2 import EntTestObject2Model  # noqa: F401
from .ent_test_object2 import EntTestObject2
from .ent_test_object import EntTestObjectModel  # noqa: F401
from .ent_test_object import EntTestObject
from .ent_test_sub_object import EntTestSubObjectModel  # noqa: F401
from .ent_test_sub_object import EntTestSubObject
from .ent_test_thing_view import EntTestThingView  # noqa: F401

UUID_TO_ENT: dict[bytes, type[Ent[ExampleViewerContext]]] = {
    b"\x43\x48": EntChild,
    b"\x3b\xdf": EntGrandParent,
    b"\x20\x33": EntParent,
    b"\x7c\x9a": EntTestObject2,
    b"\x23\x1c": EntTestObject,
    b"\x16\xd7": EntTestSubObject,
}
