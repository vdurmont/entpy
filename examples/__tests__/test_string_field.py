import pytest

from entpy import ValidationError
from evc import ExampleViewerContext
from generated.ent_test_object import (
    EntTestObjectExample,
)


async def test_string_field_too_long(vc: ExampleViewerContext) -> None:
    with pytest.raises(ValidationError):
        await EntTestObjectExample.gen_create(vc, firstname="A" * 101)
