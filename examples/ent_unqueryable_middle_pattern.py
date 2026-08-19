from entpy import Field, Pattern, StringField

from ent_unqueryable_pattern import EntUnqueryablePattern


class EntUnqueryableMiddlePattern(Pattern):
    """A queryable pattern implementing an unqueryable one.

    Its own view unions its implementations as usual; only the root pattern's
    cross-implementation query is absent. Its generated `query()` overrides
    nothing concrete -- the root leaves `EntPatternBase.query()` abstract -- so
    it must carry no `type: ignore[override]`."""

    def get_example_subclass_name(self) -> str | None:
        return "EntUnqueryableGrandchild"

    def get_patterns(self) -> list[Pattern]:
        return [EntUnqueryablePattern()]

    def get_fields(self) -> list[Field]:
        return [
            StringField("kind", 100).not_null().example("a kind"),
        ]
