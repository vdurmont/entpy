from entpy import (
    Action,
    AllowAll,
    EdgeDelegate,
    EmailField,
    PrivacyRule,
    Schema,
    StringField,
)


class EntUserSchema(Schema):
    """Example schema demonstrating EmailField usage."""

    def get_description(self):
        return "A user entity with email validation"

    def get_fields(self):
        return [
            StringField("name", 100).not_null().example("John Doe"),
            EmailField("email").not_null().example("john.doe@example.com"),
            EmailField("secondary_email").example("john.backup@example.com"),
            EmailField("contact_email").default("noreply@example.com"),
        ]

    def get_privacy_config(self, action: Action) -> list[EdgeDelegate | PrivacyRule]:
        return [AllowAll()]
