from entpy import Field, Pattern


class EntOtherSchemaPatternPattern(Pattern):
    def get_example_subclass_name(self) -> str | None:
        return "EntTestObject4"

    def get_fields(self) -> list[Field]:
        return []

    @classmethod
    def get_table_schema(cls) -> str | None:
        return "other"
