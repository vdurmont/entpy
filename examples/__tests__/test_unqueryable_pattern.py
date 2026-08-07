"""A pattern returning `is_queryable() -> False` keeps everything a pattern
gives its implementations except the cross-implementation query."""

from pathlib import Path

import pytest

from ent_unqueryable_pattern import EntUnqueryablePattern
from entpy.framework.pattern import Pattern
from entpy.gencode.pattern_generator import (
    _check_no_unique_across_implementations,
)
from evc import ExampleViewerContext
from generated.ent_test_thing import IEntTestThing
from generated.ent_unqueryable import IEntUnqueryable, IEntUnqueryableMutator
from generated.ent_unqueryable_child import (
    EntUnqueryableChild,
    EntUnqueryableChildExample,
)
from generated.ent_unqueryable_sibling import EntUnqueryableSiblingExample

_GENERATED = Path(__file__).resolve().parent.parent / "generated"


def test_patterns_are_queryable_by_default() -> None:
    class EntPlainPattern(Pattern):
        def get_fields(self) -> list:
            return []

    assert EntPlainPattern().is_queryable() is True


def test_opting_out_is_explicit() -> None:
    assert EntUnqueryablePattern().is_queryable() is False


def test_no_view_module_is_generated() -> None:
    # A queryable pattern is the control: its view is still there.
    assert (_GENERATED / "ent_test_thing_view.py").exists()
    assert not (_GENERATED / "ent_unqueryable_view.py").exists()


def test_view_is_not_imported_by_all_models() -> None:
    # all_models imports each view for its side effect of mapping the pattern
    # model, so a missing view must not leave a dangling import behind.
    all_models = (_GENERATED / "all_models.py").read_text()
    assert "ent_test_thing_view" in all_models
    assert "ent_unqueryable_view" not in all_models


def test_no_query_is_generated() -> None:
    assert hasattr(IEntTestThing, "query")
    # EntPatternBase.query() stays abstract rather than being implemented
    # against a view that does not exist.
    assert getattr(IEntUnqueryable.query, "__isabstractmethod__", False) is True


def test_the_pattern_may_span_database_schemas() -> None:
    # The two implementations live in different database schemas. A pattern's
    # table schema only reaches generated code through the view and through
    # __table_args__ on the pattern model, and this pattern has neither, so
    # nothing forces them to agree.
    from generated.ent_unqueryable import EntUnqueryableModel
    from generated.ent_unqueryable_child import EntUnqueryableChildModel
    from generated.ent_unqueryable_sibling import EntUnqueryableSiblingModel

    assert EntUnqueryableSiblingModel.__table__.schema == "other"
    assert EntUnqueryableChildModel.__table__.schema is None
    # The abstract pattern model declares no schema of its own, which is what
    # stops it from pulling an implementation into the wrong one.
    assert "__table_args__" not in vars(EntUnqueryableModel)


async def test_the_pattern_still_reaches_its_implementations(
    vc: ExampleViewerContext,
) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc, label="hello")

    fetched = await IEntUnqueryable.gen(vc, child.id)

    assert isinstance(fetched, EntUnqueryableChild)
    assert fetched.label == "hello"


async def test_the_pattern_still_carries_its_fields_to_both_implementations(
    vc: ExampleViewerContext,
) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc, label="one")
    sibling = await EntUnqueryableSiblingExample.gen_create(vc, label="two")

    assert child.label == "one"
    assert sibling.label == "two"


async def test_the_pattern_mutator_still_dispatches(
    vc: ExampleViewerContext,
) -> None:
    child = await EntUnqueryableChildExample.gen_create(vc, label="before")

    mutator = IEntUnqueryableMutator.update(vc, child)
    mutator.label = "after"
    updated = await mutator.gen_savex()

    assert updated.label == "after"


def test_unique_across_implementations_is_rejected() -> None:
    # Both unique mechanisms are enforced through the view, so opting out of
    # the view while declaring one has to fail at generation rather than at
    # migration or lookup time.
    from entpy import CompositeIndex, Field, StringField

    class EntUniqueFieldPattern(Pattern):
        def get_fields(self) -> list[Field]:
            return [StringField("key", 100).unique()]

    class EntUniqueIndexPattern(Pattern):
        def get_fields(self) -> list[Field]:
            return [StringField("a", 100), StringField("b", 100)]

        def get_composite_indexes(self) -> list[CompositeIndex]:
            return [CompositeIndex(field_names=["a", "b"], unique=True)]

    with pytest.raises(ValueError, match=r"Unique fields: \['key'\]"):
        _check_no_unique_across_implementations(
            pattern=EntUniqueFieldPattern(), base_name="EntUniqueField"
        )

    with pytest.raises(ValueError, match=r"Unique indexes: \[\['a', 'b'\]\]"):
        _check_no_unique_across_implementations(
            pattern=EntUniqueIndexPattern(), base_name="EntUniqueIndex"
        )
