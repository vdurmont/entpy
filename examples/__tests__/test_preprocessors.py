import pytest

from entpy import ValidationError
from evc import ExampleViewerContext
from generated.ent_credential import EntCredentialMutator
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)
from generated.ent_test_thing import IEntTestThing


async def test_null_bytes_are_removed_on_create(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Vi\x00ncent",  # StringField
        context="Some \x00context",  # TextField
    )

    assert ent.firstname == "Vincent"
    assert ent.context == "Some context"


async def test_null_bytes_are_removed_on_update(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc)

    mut = EntTestObjectMutator.update(vc, ent)
    mut.firstname = "Vi\x00ncent"
    ent = await mut.gen_savex()

    assert ent.firstname == "Vincent"


async def test_custom_preprocessor_runs(vc: ExampleViewerContext) -> None:
    ent = await EntTestObjectExample.gen_create(vc, preprocessed_field="  padded  ")

    assert ent.preprocessed_field == "padded"


async def test_preprocessors_run_before_validators(vc: ExampleViewerContext) -> None:
    # preprocessed_field is a StringField(100) whose preprocessor strips
    # whitespace: 108 raw characters, 100 once stripped, so the length
    # validator has to see the stripped value for this to pass.
    ent = await EntTestObjectExample.gen_create(
        vc, preprocessed_field="    " + "a" * 100 + "    "
    )
    assert ent.preprocessed_field == "a" * 100

    with pytest.raises(ValidationError):
        await EntTestObjectExample.gen_create(
            vc, preprocessed_field="    " + "a" * 101 + "    "
        )


async def test_preprocessors_run_before_triggers(vc: ExampleViewerContext) -> None:
    # The credential trigger computes `slug` from `name`; it should be handed
    # the already-cleaned name rather than the raw one.
    ent = await EntCredentialMutator.create(vc=vc, name="My \x00Credential").gen_savex()

    assert ent.name == "My Credential"
    assert ent.slug == "my-credential"


async def test_unique_lookup_is_preprocessed(vc: ExampleViewerContext) -> None:
    await EntTestObjectExample.gen_create(vc, username="vdurmont")

    found = await EntTestObject.gen_from_username(vc, "vdurmont\x00")

    assert found is not None, "the lookup value should be cleaned like the write was"
    assert found.username == "vdurmont"


async def test_pattern_unique_lookup_is_preprocessed(vc: ExampleViewerContext) -> None:
    await EntTestObjectExample.gen_create(vc, a_pattern_preprocessed_field="a-thing")

    found = await IEntTestThing.gen_from_a_pattern_preprocessed_field(vc, "a-thing\x00")

    assert found is not None, "a pattern lookup should preprocess its value too"
    assert found.a_pattern_preprocessed_field == "a-thing"
