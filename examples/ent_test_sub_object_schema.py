from framework.ent_schema import EntSchema
from framework.fields.field import Field, StringField


class EntTestSubObjectSchema(EntSchema):
    def get_fields(self) -> list[Field]:
        return [StringField("email", 100).not_null().example("vdurmont@gmail.com")]
