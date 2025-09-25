from abc import ABC


class EntField(ABC):
    name: str

    def __init__(self, name: str):
        self.name = name


class StringField(EntField):
    pass
