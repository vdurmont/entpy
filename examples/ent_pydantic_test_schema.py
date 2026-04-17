from pydantic import BaseModel

from entpy import JsonField, Schema, StringField


class AddressShape(BaseModel):
    street: str
    city: str
    zip_code: str


class ProfileShape(BaseModel):
    bio: str
    age: int
    hobbies: list[str]


class EntPydanticTestSchema(Schema):
    def get_fields(self):
        return [
            StringField("name", 100).not_null().example("John Doe"),
            JsonField("address", AddressShape)
            .not_null()
            .example(
                AddressShape(street="123 Main St", city="New York", zip_code="10001")
            ),
            JsonField("profile", ProfileShape).example(
                ProfileShape(
                    bio="Software engineer", age=30, hobbies=["coding", "reading"]
                )
            ),
            JsonField("legacy_data", "dict[str, Any]").example({"foo": "bar"}),
        ]

    def get_table_name(self):
        return "pydantic_test"

    def get_privacy_config(self, action):
        from entpy import AllowAll

        return [AllowAll()]
