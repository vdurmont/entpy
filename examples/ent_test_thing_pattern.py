from entpy import Field, Pattern, StringField, EnumField
from enum import Enum


class ThingStatus(Enum):
    GOOD = "GOOD"
    BAD = "BAD"


class EntTestThingPattern(Pattern):
    def get_fields(self) -> list[Field]:
        return [
            StringField("a_good_thing", 100).not_null().example("A sunny day"),
            EnumField("thing_status", ThingStatus),
        ]
