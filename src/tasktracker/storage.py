import json
import os
import tempfile
from pathlib import Path
from typing import List
from .models import Task


class JsonStorage:
    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)

    def save(self, tasks: List[Task]) -> None:
        data = [task.to_dict() for task in tasks]
        payload = json.dumps(data, indent=2)

        # Write to a temp file in the same directory, then atomically replace
        # the target so a crash mid-write never leaves a partial/corrupt file.
        dir_ = self.file_path.parent
        fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
            os.replace(tmp_path, self.file_path)
        except Exception:
            # Clean up the temp file if anything goes wrong before the replace.
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def load(self) -> List[Task]:
        if not self.file_path.exists():
            return []

        try:
            text = self.file_path.read_text(encoding="utf-8")
        except OSError as e:
            raise OSError(f"Could not read task file '{self.file_path}': {e}") from e

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Task file '{self.file_path}' contains invalid JSON: {e}"
            ) from e

        return [Task.from_dict(item) for item in data]
