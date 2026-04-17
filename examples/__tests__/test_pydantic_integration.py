"""Integration test for Pydantic JsonField support."""

import pytest
from pydantic import ValidationError

from ent_pydantic_test_schema import AddressShape, ProfileShape
from generated.ent_pydantic_test import EntPydanticTest, EntPydanticTestMutator


async def test_create_with_pydantic_instances(vc):
    """Test creating an entity with Pydantic model instances."""
    address = AddressShape(street="123 Main St", city="New York", zip_code="10001")
    profile = ProfileShape(
        bio="Software engineer", age=30, hobbies=["coding", "reading"]
    )

    ent = await EntPydanticTestMutator.create(
        vc, name="John Doe", address=address, profile=profile
    ).gen_savex()

    assert ent.name == "John Doe"
    assert isinstance(ent.address, AddressShape)
    assert ent.address.street == "123 Main St"
    assert ent.address.city == "New York"
    assert ent.address.zip_code == "10001"
    assert isinstance(ent.profile, ProfileShape)
    assert ent.profile.bio == "Software engineer"
    assert ent.profile.age == 30
    assert ent.profile.hobbies == ["coding", "reading"]


async def test_create_with_dicts(vc):
    """Test creating an entity with dictionaries (auto-validated)."""
    address_dict = {"street": "456 Oak Ave", "city": "Boston", "zip_code": "02101"}
    profile_dict = {"bio": "Data scientist", "age": 28, "hobbies": ["math", "stats"]}

    ent = await EntPydanticTestMutator.create(
        vc, name="Jane Smith", address=address_dict, profile=profile_dict
    ).gen_savex()

    assert ent.name == "Jane Smith"
    assert isinstance(ent.address, AddressShape)
    assert ent.address.street == "456 Oak Ave"
    assert isinstance(ent.profile, ProfileShape)
    assert ent.profile.bio == "Data scientist"


async def test_raw_properties(vc):
    """Test accessing raw dict properties."""
    address = AddressShape(street="789 Elm St", city="Seattle", zip_code="98101")

    ent = await EntPydanticTestMutator.create(
        vc, name="Bob Wilson", address=address
    ).gen_savex()

    # Test parsed property
    assert isinstance(ent.address, AddressShape)

    # Test raw property
    assert isinstance(ent.address_raw, dict)
    assert ent.address_raw["street"] == "789 Elm St"
    assert ent.address_raw["city"] == "Seattle"

    # Test nullable raw property
    assert ent.profile is None
    assert ent.profile_raw is None


async def test_update_with_pydantic_instance(vc):
    """Test updating an entity with a Pydantic instance."""
    address = AddressShape(street="Original St", city="OldCity", zip_code="00000")
    ent = await EntPydanticTestMutator.create(
        vc, name="Test User", address=address
    ).gen_savex()

    # Update with new Pydantic instance
    new_address = AddressShape(street="New St", city="NewCity", zip_code="11111")
    mutator = EntPydanticTestMutator.update(vc, ent)
    mutator.address = new_address
    updated_ent = await mutator.gen_savex()

    assert updated_ent.address.street == "New St"
    assert updated_ent.address.city == "NewCity"


async def test_update_with_dict(vc):
    """Test updating an entity with a dict."""
    address = AddressShape(street="Original St", city="OldCity", zip_code="00000")
    ent = await EntPydanticTestMutator.create(
        vc, name="Test User", address=address
    ).gen_savex()

    # Update with dict
    mutator = EntPydanticTestMutator.update(vc, ent)
    mutator.profile = {"bio": "Updated bio", "age": 35, "hobbies": ["tennis"]}
    updated_ent = await mutator.gen_savex()

    assert isinstance(updated_ent.profile, ProfileShape)
    assert updated_ent.profile.bio == "Updated bio"
    assert updated_ent.profile.age == 35


async def test_validation_error_on_invalid_dict(vc):
    """Test that invalid dicts raise validation errors."""
    # Missing required field 'zip_code'
    invalid_address = {"street": "Incomplete St", "city": "NoZip"}

    with pytest.raises(ValidationError):
        await EntPydanticTestMutator.create(
            vc, name="Invalid User", address=invalid_address
        ).gen_savex()


async def test_validation_error_on_wrong_type(vc):
    """Test that wrong types in dicts raise validation errors."""
    # Age should be int, not string
    invalid_profile = {"bio": "Test", "age": "thirty", "hobbies": []}

    address = AddressShape(street="123 St", city="City", zip_code="12345")

    with pytest.raises(ValidationError):
        await EntPydanticTestMutator.create(
            vc, name="Test User", address=address, profile=invalid_profile
        ).gen_savex()


async def test_legacy_json_field_backward_compatibility(vc):
    """Test that non-Pydantic JsonFields still work."""
    address = AddressShape(street="123 St", city="City", zip_code="12345")
    legacy_data = {"arbitrary": "data", "nested": {"key": "value"}}

    ent = await EntPydanticTestMutator.create(
        vc, name="Test User", address=address, legacy_data=legacy_data
    ).gen_savex()

    assert ent.legacy_data == legacy_data
    assert ent.legacy_data["arbitrary"] == "data"
    assert ent.legacy_data["nested"]["key"] == "value"


async def test_query_and_retrieve(vc):
    """Test querying and retrieving entities with Pydantic fields."""
    address = AddressShape(street="Query St", city="QueryCity", zip_code="99999")
    profile = ProfileShape(bio="Queryable", age=40, hobbies=["querying"])

    created = await EntPydanticTestMutator.create(
        vc, name="Query User", address=address, profile=profile
    ).gen_savex()

    # Query and retrieve
    retrieved = await EntPydanticTest.genx(vc, created.id)

    assert retrieved is not None
    assert isinstance(retrieved.address, AddressShape)
    assert retrieved.address.street == "Query St"
    assert isinstance(retrieved.profile, ProfileShape)
    assert retrieved.profile.bio == "Queryable"


async def test_nullable_pydantic_field(vc):
    """Test that nullable Pydantic fields work correctly."""
    address = AddressShape(street="123 St", city="City", zip_code="12345")

    # Create without profile (nullable)
    ent = await EntPydanticTestMutator.create(
        vc, name="No Profile User", address=address
    ).gen_savex()

    assert ent.profile is None
    assert ent.profile_raw is None

    # Update to add profile
    mutator = EntPydanticTestMutator.update(vc, ent)
    mutator.profile = ProfileShape(bio="New profile", age=25, hobbies=[])
    updated = await mutator.gen_savex()

    assert isinstance(updated.profile, ProfileShape)
    assert updated.profile.bio == "New profile"
