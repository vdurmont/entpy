from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV

from entpy.framework.database import db


def encrypt_field(id: UUID, name: str, value: bytes) -> bytes:
    return AESGCMSIV(db.encryption_key).encrypt(
        nonce=b"\x00" * 12, data=value, associated_data=id.bytes + name.encode()
    )


def decrypt_field(id: UUID, name: str, value: bytes) -> bytes:
    return AESGCMSIV(db.encryption_key).decrypt(
        nonce=b"\x00" * 12, data=value, associated_data=id.bytes + name.encode()
    )
