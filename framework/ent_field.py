from abc import ABC, abstractmethod


class EntField(ABC):
    name: str

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_python_type(self) -> str:
        raise NotImplementedError("Subclasses must implement get_python_type")


class StringField(EntField):
    def __init__(self, name: str, length: int):
        super().__init__(name=name)
        self.length = length

    def get_python_type(self) -> str:
        return "str"
