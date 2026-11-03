from enum import Enum

from entpy import SerializationConfig, TierConfig


class Tier(Enum):
    REF = "REF"
    ITEM = "ITEM"
    DETAILED = "DETAILED"


SERIALIZATION = SerializationConfig(
    tiers={
        Tier.REF: TierConfig(),
        Tier.ITEM: TierConfig(includes=Tier.REF, nested=Tier.REF),
        Tier.DETAILED: TierConfig(includes=Tier.ITEM, nested=Tier.ITEM),
    },
)
