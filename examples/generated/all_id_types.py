from hashlib import sha256



from .ent_child import EntChild
from .ent_delegate_then_rule import EntDelegateThenRule
from .ent_delegating_child import EntDelegatingChild
from .ent_delegating_grandchild import EntDelegatingGrandchild
from .ent_grand_parent import EntGrandParent
from .ent_mixed_list import EntMixedList
from .ent_parent import EntParent
from .ent_pass_then_deny import EntPassThenDeny
from .ent_privacy_parent import EntPrivacyParent
from .ent_single_rule import EntSingleRule
from .ent_test_object2 import EntTestObject2
from .ent_test_object3 import EntTestObject3
from .ent_test_object4 import EntTestObject4
from .ent_test_object5 import EntTestObject5
from .ent_test_object import EntTestObject
from .ent_test_sub_object import EntTestSubObject
from .ent_user import EntUser

# Compute type identifiers (first 2 bytes of SHA256 of class name)

_ent_child_type = sha256(EntChild.__name__.encode()).digest()[:2]
_ent_delegate_then_rule_type = sha256(EntDelegateThenRule.__name__.encode()).digest()[
    :2
]
_ent_delegating_child_type = sha256(EntDelegatingChild.__name__.encode()).digest()[:2]
_ent_delegating_grandchild_type = sha256(
    EntDelegatingGrandchild.__name__.encode()
).digest()[:2]
_ent_grand_parent_type = sha256(EntGrandParent.__name__.encode()).digest()[:2]
_ent_mixed_list_type = sha256(EntMixedList.__name__.encode()).digest()[:2]
_ent_parent_type = sha256(EntParent.__name__.encode()).digest()[:2]
_ent_pass_then_deny_type = sha256(EntPassThenDeny.__name__.encode()).digest()[:2]
_ent_privacy_parent_type = sha256(EntPrivacyParent.__name__.encode()).digest()[:2]
_ent_single_rule_type = sha256(EntSingleRule.__name__.encode()).digest()[:2]
_ent_test_object2_type = sha256(EntTestObject2.__name__.encode()).digest()[:2]
_ent_test_object3_type = sha256(EntTestObject3.__name__.encode()).digest()[:2]
_ent_test_object4_type = sha256(EntTestObject4.__name__.encode()).digest()[:2]
_ent_test_object5_type = sha256(EntTestObject5.__name__.encode()).digest()[:2]
_ent_test_object_type = sha256(EntTestObject.__name__.encode()).digest()[:2]
_ent_test_sub_object_type = sha256(EntTestSubObject.__name__.encode()).digest()[:2]
_ent_user_type = sha256(EntUser.__name__.encode()).digest()[:2]

# Map type bytes to Ent classes
ID_TYPE_MAPPING: dict[bytes, type] = {
    _ent_child_type: EntChild,
    _ent_delegate_then_rule_type: EntDelegateThenRule,
    _ent_delegating_child_type: EntDelegatingChild,
    _ent_delegating_grandchild_type: EntDelegatingGrandchild,
    _ent_grand_parent_type: EntGrandParent,
    _ent_mixed_list_type: EntMixedList,
    _ent_parent_type: EntParent,
    _ent_pass_then_deny_type: EntPassThenDeny,
    _ent_privacy_parent_type: EntPrivacyParent,
    _ent_single_rule_type: EntSingleRule,
    _ent_test_object2_type: EntTestObject2,
    _ent_test_object3_type: EntTestObject3,
    _ent_test_object4_type: EntTestObject4,
    _ent_test_object5_type: EntTestObject5,
    _ent_test_object_type: EntTestObject,
    _ent_test_sub_object_type: EntTestSubObject,
    _ent_user_type: EntUser,
}
