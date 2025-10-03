from framework.ent_field import EntField, StringField
from framework.ent_schema import EntSchema


class EntTestSubObjectSchema(EntSchema):
    def get_fields(self) -> list[EntField]:
        return [StringField("email", 100).not_null().example("vdurmont@gmail.com")]
