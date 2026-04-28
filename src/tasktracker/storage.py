import json
from pathlib import Path
from typing import List
from .models import Task


class JsonStorage:
    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)

    def save(self, tasks: List[Task]) -> None:
        data = [task.to_dict() for task in tasks]
        self.file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> List[Task]:
        if not self.file_path.exists():
            return []

        data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [Task.from_dict(item) for item in data]
