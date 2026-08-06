from uuid import UUID

from entpy import Ent

from evc import ExampleViewerContext
from .ent_model import EntModel

from .ent_child import EntChildModel  # noqa: F401
from .ent_child import EntChild
from .ent_credential import EntCredentialModel  # noqa: F401
from .ent_credential import EntCredential
from .ent_delegate_then_rule import EntDelegateThenRuleModel  # noqa: F401
from .ent_delegate_then_rule import EntDelegateThenRule
from .ent_delegating_child import EntDelegatingChildModel  # noqa: F401
from .ent_delegating_child import EntDelegatingChild
from .ent_delegating_grandchild import EntDelegatingGrandchildModel  # noqa: F401
from .ent_delegating_grandchild import EntDelegatingGrandchild
from .ent_grand_parent import EntGrandParentModel  # noqa: F401
from .ent_grand_parent import EntGrandParent
from .ent_guarded import EntGuardedModel  # noqa: F401
from .ent_guarded import EntGuarded
from .ent_inherited_test_middle_view import ent_inherited_test_middle_view  # noqa: F401
from .ent_inherited_test import EntInheritedTestModel  # noqa: F401
from .ent_inherited_test import EntInheritedTest
from .ent_inherited_test_top_view import ent_inherited_test_top_view  # noqa: F401
from .ent_mixed_list import EntMixedListModel  # noqa: F401
from .ent_mixed_list import EntMixedList
from .ent_other_schema_pattern_view import ent_other_schema_pattern_view  # noqa: F401
from .ent_parent import EntParentModel  # noqa: F401
from .ent_parent import EntParent
from .ent_pass_then_deny import EntPassThenDenyModel  # noqa: F401
from .ent_pass_then_deny import EntPassThenDeny
from .ent_policy import EntPolicyModel  # noqa: F401
from .ent_policy import EntPolicy
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
from .ent_unqueryable_child import EntUnqueryableChildModel  # noqa: F401
from .ent_unqueryable_child import EntUnqueryableChild
from .ent_unqueryable_sibling import EntUnqueryableSiblingModel  # noqa: F401
from .ent_unqueryable_sibling import EntUnqueryableSibling
from .ent_user import EntUserModel  # noqa: F401
from .ent_user import EntUser

UUID_TO_ENT: dict[bytes, type[Ent[ExampleViewerContext, EntModel]]] = {
    b"\x43\x48": EntChild,
    b"\x12\x0d": EntCredential,
    b"\x25\xcb": EntDelegateThenRule,
    b"\x49\xc2": EntDelegatingChild,
    b"\x2a\x0c": EntDelegatingGrandchild,
    b"\x3b\xdf": EntGrandParent,
    b"\x14\x8b": EntGuarded,
    b"\xb6\x61": EntInheritedTest,
    b"\x6f\xd4": EntMixedList,
    b"\x20\x33": EntParent,
    b"\xd5\x27": EntPassThenDeny,
    b"\x2f\x3a": EntPolicy,
    b"\xfe\x82": EntPrivacyParent,
    b"\x39\x63": EntSingleRule,
    b"\x7c\x9a": EntTestObject2,
    b"\x38\xe7": EntTestObject3,
    b"\x5c\x4c": EntTestObject4,
    b"\xf1\x91": EntTestObject5,
    b"\x23\x1c": EntTestObject,
    b"\x16\xd7": EntTestSubObject,
    b"\x84\x30": EntUnqueryableChild,
    b"\x43\xdb": EntUnqueryableSibling,
    b"\x01\x75": EntUser,
}


def decode_entity_type_from_id(
    entity_id: UUID,
) -> type[Ent[ExampleViewerContext, EntModel]] | None:
    uuid_type = entity_id.bytes[6:8]
    return UUID_TO_ENT.get(uuid_type)
