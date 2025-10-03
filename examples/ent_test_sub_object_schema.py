from framework.fields.core import Field
from framework.fields.string_field import StringField
from framework.schema import Schema


class EntTestSubObjectSchema(Schema):
    def get_fields(self) -> list[Field]:
        return [StringField("email", 100).not_null().example("vdurmont@gmail.com")]
