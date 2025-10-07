from entpy import Field, Schema, StringField


class EntTestSubObjectSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [StringField("email", 100).not_null().example("vdurmont@gmail.com")]
