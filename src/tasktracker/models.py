from dataclasses import dataclass, asdict


@dataclass
class Task:
    title: str
    description: str = ""
    completed: bool = False

    def mark_complete(self) -> None:
        self.completed = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)
