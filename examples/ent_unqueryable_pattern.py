from entpy import Field, Pattern, StringField


class EntUnqueryablePattern(Pattern):
    """Example pattern opting out of cross-implementation queries.

    Its fields, privacy and mutator surface reach the implementations exactly
    as a queryable pattern's do; only the view and `IUnqueryable.query()` are
    absent."""

    def get_example_subclass_name(self) -> str | None:
        return "EntUnqueryableChild"

    def is_queryable(self) -> bool:
        return False

    def get_fields(self) -> list[Field]:
        return [
            StringField("label", 100).not_null().example("a label"),
        ]
