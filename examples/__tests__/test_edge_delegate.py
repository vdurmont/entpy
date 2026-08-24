import pytest
from entpy import PrivacyError
from evc import (
    ExampleOmniscientViewerContext,
    ExampleTestViewerContext,
    ExampleViewerContext,
)
from generated.ent_delegating_child import (
    EntDelegatingChild,
    EntDelegatingChildMutator,
    EntDelegatingChildExample,
)
from generated.ent_delegating_grandchild import (
    EntDelegatingGrandchild,
    EntDelegatingGrandchildExample,
)
from generated.ent_privacy_parent import (
    EntPrivacyParent,
    EntPrivacyParentExample,
)

# ==============================================================================
# Test 1: Basic Edge Delegation
# ==============================================================================


async def test_basic_edge_delegation_with_test_viewer_context() -> None:
    """Test that a child delegates privacy to its parent and allows access with TestViewerContext."""
    vc = ExampleTestViewerContext()

    # Create a privacy parent (which allows TestViewerContext)
    parent = await EntPrivacyParentExample.gen_create(vc, name="Parent 1")
    assert parent is not None

    # Create a delegating child pointing to this parent
    child = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Child 1"
    )
    assert child is not None

    # When we fetch the child with TestViewerContext, it should be accessible
    # because it delegates to the parent, which allows TestViewerContext
    fetched_child = await EntDelegatingChild.gen(vc, child.id)
    assert fetched_child is not None
    assert fetched_child.name == "Child 1"


async def test_basic_edge_delegation_with_omniscient_viewer_context() -> None:
    """Test that a child delegates privacy to its parent and allows access with OmniscientViewerContext."""
    vc = ExampleOmniscientViewerContext()

    # Create a privacy parent (which allows OmniscientViewerContext)
    parent = await EntPrivacyParentExample.gen_create(vc, name="Parent 2")
    assert parent is not None

    # Create a delegating child pointing to this parent
    child = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Child 2"
    )
    assert child is not None

    # When we fetch the child with OmniscientViewerContext, it should be accessible
    fetched_child = await EntDelegatingChild.gen(vc, child.id)
    assert fetched_child is not None
    assert fetched_child.name == "Child 2"


async def test_basic_edge_delegation_denies_regular_viewer_context() -> None:
    """Test that a child delegates privacy to its parent and denies access with regular ViewerContext."""
    # Use TestViewerContext to create entities
    create_vc = ExampleTestViewerContext()

    # Create a privacy parent
    parent = await EntPrivacyParentExample.gen_create(create_vc, name="Parent 3")
    assert parent is not None

    # Create a delegating child
    child = await EntDelegatingChildExample.gen_create(
        create_vc, privacy_parent_id=parent.id, name="Child 3"
    )
    assert child is not None

    # Now try to fetch with regular ViewerContext (should be denied)
    regular_vc = ExampleViewerContext()
    fetched_child = await EntDelegatingChild.gen(regular_vc, child.id)
    assert fetched_child is None  # Access should be denied


async def test_action_translation() -> None:
    vc = ExampleOmniscientViewerContext()

    parent = await EntPrivacyParentExample.gen_create(vc, name="Parent 1")
    child = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Child 1"
    )

    # The parent policy does not allow UPDATE, but the EdgeDelegate should
    # translate the UPDATE check into a CREATE check on the parent.
    mut = EntDelegatingChildMutator.update(vc, child)
    mut.name = "Updated Child"
    updated_child = await mut.gen_savex()
    assert updated_child is not None
    assert updated_child.name == "Updated Child"


async def test_action_disabling() -> None:
    vc = ExampleOmniscientViewerContext()

    parent = await EntPrivacyParentExample.gen_create(vc, name="Parent 1")
    child = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Child 1"
    )

    # The parent policy allows HARD_DELETE, but the EdgeDelegate disables
    # this and so this should fail.
    with pytest.raises(PrivacyError):
        await EntDelegatingChildMutator.hard_delete(vc, child).gen_save()


# ==============================================================================
# Test 2: Multi-Level Delegation Chain
# ==============================================================================


async def test_multi_level_delegation_with_test_viewer_context() -> None:
    """Test that privacy evaluation traverses a multi-level delegation chain."""
    vc = ExampleTestViewerContext()

    # Create the chain: Grandchild → Child → Parent
    parent = await EntPrivacyParentExample.gen_create(vc, name="Root Parent")
    assert parent is not None

    child = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Middle Child"
    )
    assert child is not None

    grandchild = await EntDelegatingGrandchildExample.gen_create(
        vc, delegating_child_id=child.id, name="Leaf Grandchild"
    )
    assert grandchild is not None

    # Fetch the grandchild - it should delegate to child, which delegates to parent
    # The parent allows TestViewerContext, so the grandchild should be accessible
    fetched_grandchild = await EntDelegatingGrandchild.gen(vc, grandchild.id)
    assert fetched_grandchild is not None
    assert fetched_grandchild.name == "Leaf Grandchild"


async def test_multi_level_delegation_with_omniscient_viewer_context() -> None:
    """Test multi-level delegation with OmniscientViewerContext."""
    vc = ExampleOmniscientViewerContext()

    # Create the chain
    parent = await EntPrivacyParentExample.gen_create(vc, name="Root Parent 2")
    child = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Middle Child 2"
    )
    grandchild = await EntDelegatingGrandchildExample.gen_create(
        vc, delegating_child_id=child.id, name="Leaf Grandchild 2"
    )

    # Fetch with OmniscientViewerContext
    fetched_grandchild = await EntDelegatingGrandchild.gen(vc, grandchild.id)
    assert fetched_grandchild is not None
    assert fetched_grandchild.name == "Leaf Grandchild 2"


async def test_multi_level_delegation_denies_regular_viewer_context() -> None:
    """Test that multi-level delegation properly denies access with regular ViewerContext."""
    create_vc = ExampleTestViewerContext()

    # Create the chain
    parent = await EntPrivacyParentExample.gen_create(create_vc, name="Root Parent 3")
    child = await EntDelegatingChildExample.gen_create(
        create_vc, privacy_parent_id=parent.id, name="Middle Child 3"
    )
    grandchild = await EntDelegatingGrandchildExample.gen_create(
        create_vc, delegating_child_id=child.id, name="Leaf Grandchild 3"
    )

    # Try to fetch with regular ViewerContext
    regular_vc = ExampleViewerContext()
    fetched_grandchild = await EntDelegatingGrandchild.gen(regular_vc, grandchild.id)
    assert fetched_grandchild is None  # Should be denied


# ==============================================================================
# Test 3: Delegation with Different Viewer Contexts
# ==============================================================================


async def test_parent_accessible_child_accessible() -> None:
    """When parent is accessible to a viewer context, child should also be accessible."""
    vc = ExampleTestViewerContext()

    parent = await EntPrivacyParentExample.gen_create(vc, name="Accessible Parent")
    child = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Should Be Accessible Child"
    )

    # Both should be accessible
    fetched_parent = await EntPrivacyParent.gen(vc, parent.id)
    fetched_child = await EntDelegatingChild.gen(vc, child.id)

    assert fetched_parent is not None
    assert fetched_child is not None


async def test_parent_not_accessible_child_not_accessible() -> None:
    """When parent is not accessible to a viewer context, child should also not be accessible."""
    create_vc = ExampleTestViewerContext()
    read_vc = ExampleViewerContext()  # Regular VC that parent doesn't allow

    parent = await EntPrivacyParentExample.gen_create(
        create_vc, name="Inaccessible Parent"
    )
    child = await EntDelegatingChildExample.gen_create(
        create_vc, privacy_parent_id=parent.id, name="Should Be Inaccessible Child"
    )

    # Neither should be accessible with regular ViewerContext
    fetched_parent = await EntPrivacyParent.gen(read_vc, parent.id)
    fetched_child = await EntDelegatingChild.gen(read_vc, child.id)

    assert fetched_parent is None
    assert fetched_child is None


async def test_different_children_same_parent_same_privacy() -> None:
    """Multiple children delegating to the same parent should have the same privacy rules."""
    vc = ExampleTestViewerContext()

    # Create one parent
    parent = await EntPrivacyParentExample.gen_create(vc, name="Shared Parent")

    # Create multiple children delegating to the same parent
    child1 = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Child 1"
    )
    child2 = await EntDelegatingChildExample.gen_create(
        vc, privacy_parent_id=parent.id, name="Child 2"
    )

    # Both children should be accessible with TestViewerContext
    fetched_child1 = await EntDelegatingChild.gen(vc, child1.id)
    fetched_child2 = await EntDelegatingChild.gen(vc, child2.id)

    assert fetched_child1 is not None
    assert fetched_child2 is not None

    # Both should be inaccessible with regular ViewerContext
    regular_vc = ExampleViewerContext()
    fetched_child1_regular = await EntDelegatingChild.gen(regular_vc, child1.id)
    fetched_child2_regular = await EntDelegatingChild.gen(regular_vc, child2.id)

    assert fetched_child1_regular is None
    assert fetched_child2_regular is None
