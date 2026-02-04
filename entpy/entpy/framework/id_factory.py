import struct
from datetime import datetime
from hashlib import sha256
from secrets import token_bytes
from time import time
from typing import TYPE_CHECKING
from uuid import UUID

from entpy.framework.errors import ValidationError

if TYPE_CHECKING:
    from entpy.framework.ent import Ent


def generate_uuid(
    entity_type: type["Ent"], uuid_datetime: datetime | None = None
) -> UUID:
    """
    Our UUIDs are composed of the following:
    6 bytes: Unix timestamp in milliseconds, big-endian
    2 bytes: Object type, first 2 bytes of SHA256 hash of table name
    2 bytes: Reserved for future use as a shard ID, currently \x00\x00
    6 bytes: Random bytes
    """
    uuid_type = sha256(entity_type.__name__.encode()).digest()[:2]
    timestamp = uuid_datetime.timestamp() if uuid_datetime else time()
    return UUID(
        bytes=struct.pack("!Q", int(timestamp * 1000))[2:]
        + uuid_type
        + b"\x00\x00"
        + token_bytes(6)
    )


def validate_ent_id(ent_id: UUID | str) -> UUID:
    # Convert str to UUID if needed
    if isinstance(ent_id, str):
        try:
            return UUID(ent_id)
        except ValueError as e:
            raise ValidationError(f"Invalid ID format for {ent_id}") from e
    return ent_id
