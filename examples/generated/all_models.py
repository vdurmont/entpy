from entpy import Ent

from evc import ExampleViewerContext
from .ent_model import EntModel

from .ent_child import EntChildModel  # noqa: F401
from .ent_child import EntChild
from .ent_delegate_then_rule import EntDelegateThenRuleModel  # noqa: F401
from .ent_delegate_then_rule import EntDelegateThenRule
from .ent_delegating_child import EntDelegatingChildModel  # noqa: F401
from .ent_delegating_child import EntDelegatingChild
from .ent_delegating_grandchild import EntDelegatingGrandchildModel  # noqa: F401
from .ent_delegating_grandchild import EntDelegatingGrandchild
from .ent_grand_parent import EntGrandParentModel  # noqa: F401
from .ent_grand_parent import EntGrandParent
from .ent_mixed_list import EntMixedListModel  # noqa: F401
from .ent_mixed_list import EntMixedList
from .ent_parent import EntParentModel  # noqa: F401
from .ent_parent import EntParent
from .ent_pass_then_deny import EntPassThenDenyModel  # noqa: F401
from .ent_pass_then_deny import EntPassThenDeny
from .ent_privacy_parent import EntPrivacyParentModel  # noqa: F401
from .ent_privacy_parent import EntPrivacyParent
from .ent_single_rule import EntSingleRuleModel  # noqa: F401
from .ent_single_rule import EntSingleRule
from .ent_test_object2 import EntTestObject2Model  # noqa: F401
from .ent_test_object2 import EntTestObject2
from .ent_test_object3 import EntTestObject3Model  # noqa: F401
from .ent_test_object3 import EntTestObject3
from .ent_test_object4 import EntTestObject4Model  # noqa: F401
from .ent_test_object4 import EntTestObject4
from .ent_test_object5 import EntTestObject5Model  # noqa: F401
from .ent_test_object5 import EntTestObject5
from .ent_test_object import EntTestObjectModel  # noqa: F401
from .ent_test_object import EntTestObject
from .ent_test_pattern_view import ent_test_pattern_view  # noqa: F401
from .ent_test_sub_object import EntTestSubObjectModel  # noqa: F401
from .ent_test_sub_object import EntTestSubObject
from .ent_test_thing_view import ent_test_thing_view  # noqa: F401

UUID_TO_ENT: dict[bytes, type[Ent[ExampleViewerContext, EntModel]]] = {
    b"\x43\x48": EntChild,
    b"\x25\xcb": EntDelegateThenRule,
    b"\x49\xc2": EntDelegatingChild,
    b"\x2a\x0c": EntDelegatingGrandchild,
    b"\x3b\xdf": EntGrandParent,
    b"\x6f\xd4": EntMixedList,
    b"\x20\x33": EntParent,
    b"\xd5\x27": EntPassThenDeny,
    b"\xfe\x82": EntPrivacyParent,
    b"\x39\x63": EntSingleRule,
    b"\x7c\x9a": EntTestObject2,
    b"\x38\xe7": EntTestObject3,
    b"\x5c\x4c": EntTestObject4,
    b"\xf1\x91": EntTestObject5,
    b"\x23\x1c": EntTestObject,
    b"\x16\xd7": EntTestSubObject,
}
