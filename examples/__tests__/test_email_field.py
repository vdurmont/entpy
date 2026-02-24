import pytest
from evc import ExampleViewerContext
from entpy import ValidationError
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
)


async def test_email_field_with_valid_email(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField accepts valid email addresses."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Alice")

    assert ent.email is not None, "email should be set from example"
    assert isinstance(ent.email, str), "email should be a string"
    assert ent.email == "test@example.com", "email should match the example value"


async def test_email_field_with_custom_valid_email(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField accepts custom valid email addresses."""
    custom_email = "alice@wonderland.com"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Alice",
        email=custom_email,
    )

    assert ent.email == custom_email, "email should match the custom value"


async def test_email_field_with_invalid_email(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField rejects invalid email addresses."""
    with pytest.raises(ValidationError):
        await EntTestObjectExample.gen_create(
            vc,
            firstname="Bob",
            email="not-an-email",
        )


async def test_email_field_with_missing_at_sign(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField rejects emails without @ sign."""
    with pytest.raises(ValidationError):
        await EntTestObjectExample.gen_create(
            vc,
            firstname="Charlie",
            email="notemail.com",
        )


async def test_email_field_with_missing_domain(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField rejects emails without domain."""
    with pytest.raises(ValidationError):
        await EntTestObjectExample.gen_create(
            vc,
            firstname="David",
            email="test@",
        )


async def test_email_field_with_none(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField accepts None when nullable."""
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Eve",
        email=None,
    )

    assert ent.email is None, "email should be None when explicitly set"


async def test_email_field_persists_after_reload(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField values persist after reloading the entity."""
    custom_email = "frank@example.com"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Frank",
        email=custom_email,
    )

    # Reload the entity
    reloaded = await EntTestObject.genx(vc, ent.id)

    assert reloaded.email == custom_email, "email should persist after reloading"


async def test_email_field_with_default_value(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField with default value uses the default when not provided."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="George")

    assert ent.contact_email is not None, "contact_email should be set from default"
    assert isinstance(ent.contact_email, str), "contact_email should be a string"
    assert ent.contact_email == "support@example.com", (
        "contact_email should match the default value"
    )


async def test_email_field_default_can_be_overridden(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField default value can be overridden with a custom value."""
    custom_email = "custom@example.com"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Hannah",
        contact_email=custom_email,
    )

    assert ent.contact_email == custom_email, (
        "contact_email should match the custom value"
    )


async def test_email_field_with_subdomain(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField accepts emails with subdomains."""
    email_with_subdomain = "user@mail.example.com"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Ian",
        email=email_with_subdomain,
    )

    assert ent.email == email_with_subdomain, "email should accept subdomains"


async def test_email_field_with_plus_addressing(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField accepts emails with plus addressing."""
    email_with_plus = "user+tag@example.com"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Jane",
        email=email_with_plus,
    )

    assert ent.email == email_with_plus, "email should accept plus addressing"


async def test_email_field_with_invalid_override_of_default(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField validates even when overriding default."""
    with pytest.raises(ValidationError):
        await EntTestObjectExample.gen_create(
            vc,
            firstname="Kevin",
            contact_email="invalid-email",
        )


async def test_email_field_normalizes_to_lowercase(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField normalizes emails to lowercase."""
    uppercase_email = "USER@EXAMPLE.COM"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Lisa",
        email=uppercase_email,
    )

    assert ent.email == "user@example.com", "email should be normalized to lowercase"


async def test_email_field_normalizes_mixed_case(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField normalizes mixed case emails."""
    mixed_case_email = "User.Name@Example.COM"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Mike",
        email=mixed_case_email,
    )

    assert ent.email == "user.name@example.com", (
        "email should be normalized to lowercase"
    )


async def test_email_field_normalization_persists(
    vc: ExampleViewerContext,
) -> None:
    """Test that normalized email values persist after reloading."""
    uppercase_email = "NORMALIZED@EXAMPLE.COM"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Nancy",
        email=uppercase_email,
    )

    # Reload the entity
    reloaded = await EntTestObject.genx(vc, ent.id)

    assert reloaded.email == "normalized@example.com", (
        "normalized email should persist after reloading"
    )


async def test_email_field_normalizes_default_override(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField normalizes when overriding default values."""
    uppercase_email = "CUSTOM@EXAMPLE.COM"
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Oliver",
        contact_email=uppercase_email,
    )

    assert ent.contact_email == "custom@example.com", (
        "contact_email should be normalized even when overriding default"
    )


async def test_email_field_normalizes_on_update(
    vc: ExampleViewerContext,
) -> None:
    """Test that EmailField normalizes emails during updates."""
    from generated.ent_test_object import EntTestObjectMutator

    # Create entity with lowercase email
    ent = await EntTestObjectExample.gen_create(
        vc,
        firstname="Paul",
        email="paul@example.com",
    )

    # Update with uppercase email
    mut = EntTestObjectMutator.update(vc, ent)
    mut.email = "UPDATED@EXAMPLE.COM"
    updated_ent = await mut.gen_savex()

    assert updated_ent.email == "updated@example.com", (
        "email should be normalized during update"
    )
