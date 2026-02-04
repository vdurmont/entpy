from entpy import Field, Pattern


class EntTestPatternPattern(Pattern):
    def get_example_subclass_name(self) -> str | None:
        return "EntTestObject2"

    def get_fields(self) -> list[Field]:
        return []
