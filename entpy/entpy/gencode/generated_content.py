from dataclasses import dataclass, field


@dataclass
class GeneratedContent:
    code: str
    imports: list[str] = field(default_factory=list)
