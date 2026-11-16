from enum import Enum

from entpy import SerializationConfig, TierConfig


class Tier(Enum):
    ITEM = "ITEM"
    DETAILED = "DETAILED"


SERIALIZATION = SerializationConfig(
    tiers={
        Tier.ITEM: TierConfig(nested=Tier.ITEM),
        Tier.DETAILED: TierConfig(includes=Tier.ITEM, nested=Tier.ITEM),
    },
)
