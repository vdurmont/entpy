from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class TierConfig:
    includes: Enum | None = None
    nested: Enum | None = None


@dataclass(frozen=True)
class FieldSerialization:
    tier: Enum
    name: str | None = None
    nested: Enum | None = None


class SerializationConfig:
    """The serialization tiers of a project, ordered from the cheapest up.

    A tier contains every field of the tier it `includes`. An edge serialized
    in a tier renders at that tier's `nested` tier, unless the field overrides
    it.
    """

    tiers: dict[Enum, TierConfig]
    tier_enum: type[Enum]

    def __init__(self, tiers: dict[Enum, TierConfig]) -> None:
        if not tiers:
            raise ValueError("A serialization config needs at least one tier.")
        enum_types = {type(tier) for tier in tiers}
        if len(enum_types) > 1:
            raise ValueError("All serialization tiers must belong to the same enum.")
        tier_enum = enum_types.pop()
        missing = [tier.name for tier in tier_enum if tier not in tiers]
        if missing:
            raise ValueError(
                f"Every member of {tier_enum.__name__} needs a TierConfig, "
                + f"missing: {', '.join(missing)}"
            )
        self.tiers = tiers
        self.tier_enum = tier_enum
        self._validate_references()
        self._validate_single_chain()

    def get_chain(self, tier: Enum) -> list[Enum]:
        chain = [tier]
        included = self.tiers[tier].includes
        while included is not None:
            if included in chain:
                raise ValueError("Serialization tiers include each other in a cycle.")
            chain.insert(0, included)
            included = self.tiers[included].includes
        return chain

    def get_ordered_tiers(self) -> list[Enum]:
        return max((self.get_chain(tier) for tier in self.tiers), key=len)

    def get_tiers_including(self, tier: Enum) -> list[Enum]:
        return [t for t in self.get_ordered_tiers() if tier in self.get_chain(t)]

    def _validate_references(self) -> None:
        for tier, config in self.tiers.items():
            for label, ref in (
                ("includes", config.includes),
                ("nested", config.nested),
            ):
                if ref is not None and ref not in self.tiers:
                    raise ValueError(
                        f"Tier {tier.name} {label} {ref!r}, which is not a tier."
                    )
            if config.includes == tier:
                raise ValueError(f"Tier {tier.name} cannot include itself.")

    def _validate_single_chain(self) -> None:
        roots = [tier for tier, config in self.tiers.items() if config.includes is None]
        if len(roots) != 1:
            raise ValueError(
                "Serialization tiers must form a single chain with one base tier, "
                + f"found {len(roots)}: {', '.join(t.name for t in roots)}"
            )
        included = [c.includes for c in self.tiers.values() if c.includes is not None]
        duplicates = {tier.name for tier in included if included.count(tier) > 1}
        if duplicates:
            raise ValueError(
                "Serialization tiers must form a single chain, but several tiers "
                + f"include {', '.join(sorted(duplicates))}"
            )
        for tier in self.tiers:
            self.get_chain(tier)
