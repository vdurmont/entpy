from abc import ABC


class EntField(ABC):
    name: str

    def __init__(self, name: str):
        self.name = name


class StringField(EntField):
    def __init__(self, name: str, length: int):
        super().__init__(name=name)
        self.length = length
