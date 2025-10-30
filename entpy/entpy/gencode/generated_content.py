from dataclasses import dataclass, field


@dataclass
class GeneratedContent:
    code: str
    imports: list[str] = field(default_factory=list)
    type_checking_imports: list[str] = field(default_factory=list)
