from entpy import Field, Pattern, StringField


class EntTestThingPattern(Pattern):
    def get_fields(self) -> list[Field]:
        return [StringField("a_good_thing", 100).not_null().example("A sunny day")]
