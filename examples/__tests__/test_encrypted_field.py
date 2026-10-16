from sqlalchemy import text
from evc import ExampleViewerContext
from generated.ent_test_object import (
    EntTestObject,
    EntTestObjectExample,
    EntTestObjectMutator,
)

from entpy import Action, AllowAll, BytesField, EdgeDelegate, Field, PrivacyRule, Schema
from entpy.framework.crypto import decrypt_field
from entpy.framework.database import db
from entpy.gencode.model_generator import generate

SECRET = b"correct horse battery staple"

# AES-GCM-SIV appends a 128-bit tag to the ciphertext.
TAG_SIZE = 16


async def _gen_stored_bytes(ent: EntTestObject) -> bytes:
    """Read the column directly, bypassing the model's decrypting property."""
    result = await db.session.execute(
        text("SELECT encrypt FROM test_object WHERE id = :id"),
        {"id": str(ent.id)},
    )
    row = result.one_or_none()
    assert row is not None, "no test_object row was persisted"
    return row[0]


async def test_encrypted_field_is_not_stored_in_plaintext(
    vc: ExampleViewerContext,
) -> None:
    """Test that an encrypted BytesField is written to the database as ciphertext."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Alice", encrypt=SECRET)

    stored = await _gen_stored_bytes(ent)

    assert stored != SECRET, "the field should not be stored as plaintext"
    assert SECRET not in stored, "the plaintext should not appear in the stored bytes"
    assert len(stored) == len(SECRET) + TAG_SIZE, (
        "stored bytes should be the ciphertext plus an authentication tag"
    )


async def test_stored_ciphertext_decrypts_to_plaintext(
    vc: ExampleViewerContext,
) -> None:
    """Test that the bytes on disk decrypt back to the original value."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Bob", encrypt=SECRET)

    stored = await _gen_stored_bytes(ent)

    assert decrypt_field(ent.id, "encrypt", stored) == SECRET, (
        "stored bytes should decrypt to the original plaintext"
    )


async def test_encrypted_field_decrypts_after_reload(
    vc: ExampleViewerContext,
) -> None:
    """Test that reading the field back from the database returns the plaintext."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Charlie", encrypt=SECRET)

    # Drop the identity map so the reload is served from the database rather
    # than the in-memory model that still holds the decrypted value.
    db.session.expunge_all()
    db.session.info.clear()
    reloaded = await EntTestObject.genx(vc, ent.id)

    assert reloaded.encrypt == SECRET, "the field should decrypt on read"


async def test_encrypted_field_can_be_updated(
    vc: ExampleViewerContext,
) -> None:
    """Test that updating an encrypted field re-encrypts the new value."""
    ent = await EntTestObjectExample.gen_create(vc, firstname="Dave", encrypt=SECRET)
    updated_secret = b"a different secret"

    mut = EntTestObjectMutator.update(vc, ent)
    mut.encrypt = updated_secret
    ent = await mut.gen_savex()

    assert ent.encrypt == updated_secret, "the field should reflect the update"
    stored = await _gen_stored_bytes(ent)
    assert updated_secret not in stored, "the new value should be stored encrypted"
    assert decrypt_field(ent.id, "encrypt", stored) == updated_secret, (
        "stored bytes should decrypt to the updated plaintext"
    )


class _EncryptedSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            BytesField("optional_secret").encrypt(),
            BytesField("required_secret").not_null().encrypt().example(b"required"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]


def test_encrypted_properties_match_nullability() -> None:
    """The generated setter is annotated, and a required field does not return None."""
    code = generate(_EncryptedSchema(), "Encrypted").code

    assert "def optional_secret(self) -> bytes | None:" in code
    assert "def optional_secret(self, value: bytes | None) -> None:" in code
    assert "def required_secret(self) -> bytes:" in code
    assert "def required_secret(self, value: bytes) -> None:" in code

    optional = code.split("def optional_secret(self) -> bytes | None:", 1)[1]
    optional = optional.split("@optional_secret.setter", 1)[0]
    required = code.split("def required_secret(self) -> bytes:", 1)[1]
    required = required.split("@required_secret.setter", 1)[0]
    assert "else None" in optional
    assert "else None" not in required
