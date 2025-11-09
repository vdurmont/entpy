def generate(base_name: str) -> str:
    return f"""def _get_field(field_name: str) -> Field:
        schema = {base_name}Schema()
        fields = schema.get_fields()
        field = list(
            filter(
                lambda field: field.name == field_name or field.original_name == field_name,
                fields,
            )
        )[0]
        if not field:
            raise ValueError(f"Unknown field: {{field_name}}")
        return field
"""
