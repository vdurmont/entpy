import random
from entpy import Field, Pattern, IntField


class EntTestPatternPattern(Pattern):
    def get_example_subclass_name(self) -> str | None:
        return "EntTestObject2"

    def get_fields(self) -> list[Field]:
        return [
            IntField("limit")
            .unique(pattern=False)
            .dynamic_example(lambda: random.randint(1, 1000))
        ]

    def get_event_fields(self) -> list[str]:
        return ["id", "limit"]
