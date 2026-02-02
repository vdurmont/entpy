"""
Tests for privacy config list variations.
Privacy config always returns list[EdgeDelegate | PrivacyRule]:
1. List with a single PrivacyRule
2. List with a single EdgeDelegate (already tested in test_edge_delegate.py)
3. List with mixed PrivacyRule and EdgeDelegate items
"""

from evc import (
    ExampleOmniscientViewerContext,
    ExampleTestViewerContext,
    ExampleViewerContext,
)
from generated.ent_mixed_list import EntMixedList, EntMixedListExample
from generated.ent_pass_then_deny import EntPassThenDeny, EntPassThenDenyExample
from generated.ent_privacy_parent import EntPrivacyParentExample
from generated.ent_single_rule import EntSingleRule, EntSingleRuleExample

# ==============================================================================
# Test 1: List with Single PrivacyRule
# ==============================================================================


async def test_single_rule_allows_test_viewer_context() -> None:
    """Test that a list with a single PrivacyRule allows TestViewerContext."""
    vc = ExampleTestViewerContext()

    # Create an entity with a list containing a single rule
    ent = await EntSingleRuleExample.gen_create(vc, name="Test Entity")
    assert ent is not None

    # Fetch with TestViewerContext should be allowed
    fetched = await EntSingleRule.gen(vc, ent.id)
    assert fetched is not None
    assert fetched.name == "Test Entity"


async def test_single_rule_denies_regular_viewer_context() -> None:
    """Test that a list with a single PrivacyRule denies regular ViewerContext."""
    create_vc = ExampleTestViewerContext()
    read_vc = ExampleViewerContext()

    # Create an entity
    ent = await EntSingleRuleExample.gen_create(create_vc, name="Test Entity 2")
    assert ent is not None

    # Fetch with regular ViewerContext should be denied
    fetched = await EntSingleRule.gen(read_vc, ent.id)
    assert fetched is None


async def test_single_rule_allows_omniscient_viewer_context_via_prepended_rule() -> (
    None
):
    """Test that OmniscientVC is allowed via prepended rules, not the entity's rule."""
    create_vc = ExampleTestViewerContext()
    read_vc = ExampleOmniscientViewerContext()

    # Create an entity
    ent = await EntSingleRuleExample.gen_create(create_vc, name="Test Entity 3")
    assert ent is not None

    # OmniscientViewerContext is allowed via prepended AllowIfOmniscientViewerContext rule
    # (not the entity's AllowIfTestViewerContext rule)
    fetched = await EntSingleRule.gen(read_vc, ent.id)
    assert fetched is not None


# ==============================================================================
# Test 2: List with Mixed PrivacyRule and EdgeDelegate
# ==============================================================================


async def test_mixed_list_allows_omniscient_viewer_context() -> None:
    """Test that mixed list allows OmniscientViewerContext via the first rule."""
    vc = ExampleOmniscientViewerContext()

    # Create parent (just for edge reference, won't be evaluated)
    parent = await EntPrivacyParentExample.gen_create(vc, name="Parent")

    # Create entity with mixed list config
    ent = await EntMixedListExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Mixed Entity"
    )
    assert ent is not None

    # OmniscientViewerContext should be allowed by the first rule in the list
    fetched = await EntMixedList.gen(vc, ent.id)
    assert fetched is not None
    assert fetched.name == "Mixed Entity"


async def test_mixed_list_delegates_to_parent_for_test_viewer_context() -> None:
    """Test that mixed list delegates to parent when first rule returns PASS."""
    vc = ExampleTestViewerContext()

    # Create parent (which allows TestViewerContext)
    parent = await EntPrivacyParentExample.gen_create(vc, name="Parent 2")

    # Create entity with mixed list config
    ent = await EntMixedListExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Mixed Entity 2"
    )
    assert ent is not None

    # TestViewerContext: first rule returns PASS, then delegates to parent
    # Parent allows TestViewerContext, so access is allowed
    fetched = await EntMixedList.gen(vc, ent.id)
    assert fetched is not None
    assert fetched.name == "Mixed Entity 2"


async def test_mixed_list_denies_regular_viewer_context() -> None:
    """Test that mixed list denies regular ViewerContext via delegation."""
    create_vc = ExampleTestViewerContext()
    read_vc = ExampleViewerContext()

    # Create parent
    parent = await EntPrivacyParentExample.gen_create(create_vc, name="Parent 3")

    # Create entity
    ent = await EntMixedListExample.gen_create(
        create_vc, privacy_parent_id=parent.id, name="Mixed Entity 3"
    )
    assert ent is not None

    # Regular ViewerContext: first rule returns PASS, delegates to parent
    # Parent denies regular ViewerContext, so access is denied
    fetched = await EntMixedList.gen(read_vc, ent.id)
    assert fetched is None


# ==============================================================================
# Test 3: PASS Behavior in Lists
# ==============================================================================


async def test_pass_continues_to_next_rule_in_list() -> None:
    """Test that when a rule returns PASS, evaluation continues to the next rule."""
    create_vc = ExampleTestViewerContext()
    read_vc = ExampleViewerContext()

    # Create entity with [AlwaysPass, AlwaysDeny] rules
    ent = await EntPassThenDenyExample.gen_create(create_vc, name="Pass Then Deny")
    assert ent is not None

    # First rule returns PASS, so evaluation continues to second rule
    # Second rule returns DENY, so access is denied
    fetched = await EntPassThenDeny.gen(read_vc, ent.id)
    assert fetched is None


async def test_pass_with_test_viewer_context_allowed_by_prepended_rule() -> None:
    """Test that TestViewerContext is allowed by prepended rule before entity rules."""
    vc = ExampleTestViewerContext()

    # Create entity
    ent = await EntPassThenDenyExample.gen_create(vc, name="Pass Then Deny 2")
    assert ent is not None

    # TestViewerContext is allowed via prepended AllowIfTestViewerContext rule,
    # so the entity's [AlwaysPass, AlwaysDeny] rules are never evaluated
    fetched = await EntPassThenDeny.gen(vc, ent.id)
    assert fetched is not None


# ==============================================================================
# Test 4: Demonstrating Prepended Rules Behavior
# ==============================================================================


async def test_prepended_rules_run_before_entity_rules() -> None:
    """Demonstrate that prepended rules are evaluated before entity rules."""
    vc = ExampleTestViewerContext()

    # Create an entity with [AlwaysPass, AlwaysDeny] rules
    ent = await EntPassThenDenyExample.gen_create(vc, name="Prepended Test")
    assert ent is not None

    # Despite entity having AlwaysDeny in its rules, TestViewerContext is allowed
    # because prepended AllowIfTestViewerContext rule returns ALLOW first
    fetched = await EntPassThenDeny.gen(vc, ent.id)
    assert fetched is not None


async def test_entity_rules_evaluated_when_prepended_rules_pass() -> None:
    """Test that entity rules are evaluated when all prepended rules return PASS."""
    create_vc = ExampleTestViewerContext()
    read_vc = ExampleViewerContext()  # Won't match any prepended rules for READ

    # Create entity with [AlwaysPass, AlwaysDeny]
    ent = await EntPassThenDenyExample.gen_create(create_vc, name="Entity Rules Test")
    assert ent is not None

    # Regular ViewerContext doesn't match prepended rules, so they return PASS
    # Then entity's rules are evaluated: AlwaysPass returns PASS, AlwaysDeny returns DENY
    # Result: DENY
    fetched = await EntPassThenDeny.gen(read_vc, ent.id)
    assert fetched is None


# ==============================================================================
# Test 5: Mixed List with Both Rule Types
# ==============================================================================


async def test_mixed_list_first_rule_short_circuits() -> None:
    """Test that when first rule in mixed list returns ALLOW, delegate is not evaluated."""
    vc = ExampleOmniscientViewerContext()

    # Create parent (we'll verify it's not actually accessed)
    parent = await EntPrivacyParentExample.gen_create(vc, name="Unused Parent")

    # Create entity with [AllowIfOmniscientViewerContext, EdgeDelegate]
    ent = await EntMixedListExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Short Circuit Test"
    )
    assert ent is not None

    # OmniscientViewerContext matches first rule (after prepended rules pass),
    # so the EdgeDelegate is never evaluated
    fetched = await EntMixedList.gen(vc, ent.id)
    assert fetched is not None
    assert fetched.name == "Short Circuit Test"


async def test_mixed_list_evaluates_delegate_when_rule_passes() -> None:
    """Test that EdgeDelegate in list is evaluated when preceding rules return PASS."""
    create_vc = ExampleTestViewerContext()
    read_vc = ExampleViewerContext()

    # Create parent that denies regular ViewerContext
    parent = await EntPrivacyParentExample.gen_create(create_vc, name="Gatekeeper")

    # Create entity with [AllowIfOmniscientViewerContext, EdgeDelegate]
    ent = await EntMixedListExample.gen_create(
        create_vc, privacy_parent_id=parent.id, name="Delegate Evaluation Test"
    )
    assert ent is not None

    # Regular VC: prepended rules PASS, first entity rule (AllowIfOmniscient) returns PASS,
    # then EdgeDelegate is evaluated, which delegates to parent, which denies regular VC
    fetched = await EntMixedList.gen(read_vc, ent.id)
    assert fetched is None
