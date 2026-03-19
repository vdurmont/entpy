from entpy import Field, Pattern, StringField


class EntInheritedTestTopPattern(Pattern):
    def get_fields(self) -> list[Field]:
        return [
            StringField("base_field", 100).not_null().example("base value"),
        ]
