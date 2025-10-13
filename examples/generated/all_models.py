from entpy import Ent

from .ent_test_object import EntTestObjectModel  # noqa: F401
from .ent_test_object import EntTestObject
from .ent_child import EntChildModel  # noqa: F401
from .ent_child import EntChild
from .ent_test_sub_object import EntTestSubObjectModel  # noqa: F401
from .ent_test_sub_object import EntTestSubObject
from .ent_parent import EntParentModel  # noqa: F401
from .ent_parent import EntParent
from .ent_grand_parent import EntGrandParentModel  # noqa: F401
from .ent_grand_parent import EntGrandParent

UUID_TO_ENT: dict[bytes, type[Ent]] = {
    b"\x23\x1c": EntTestObject,
    b"\x43\x48": EntChild,
    b"\x16\xd7": EntTestSubObject,
    b"\x20\x33": EntParent,
    b"\x3b\xdf": EntGrandParent,
}
