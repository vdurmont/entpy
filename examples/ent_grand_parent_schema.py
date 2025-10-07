from entpy import Field, Schema, StringField


class EntGrandParentSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [
            StringField("name", 100).not_null().example("Anne"),
        ]
