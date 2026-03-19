from entpy import Field, IntField, Pattern

from ent_inherited_test_top_pattern import EntInheritedTestTopPattern


class EntInheritedTestMiddlePattern(Pattern):
    def get_patterns(self) -> list[Pattern]:
        return [EntInheritedTestTopPattern()]

    def get_fields(self) -> list[Field]:
        return [
            IntField("middle_field").not_null().example(42),
        ]
