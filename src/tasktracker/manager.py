from typing import List
from .models import Task


class TaskManager:
    def __init__(self) -> None:
        self._tasks: List[Task] = []

    def add_task(self, title: str, description: str = "") -> Task:
        task = Task(title=title, description=description)
        self._tasks.append(task)
        return task

    def list_tasks(self) -> List[Task]:
        return self._tasks.copy()

    def complete_task(self, index: int) -> Task:
        task = self._tasks[index]
        task.mark_complete()
        return task

    def remove_task(self, index: int) -> Task:
        return self._tasks.pop(index)

    def get_pending_tasks(self) -> List[Task]:
        return [task for task in self._tasks if not task.completed]
    
    def get_pending_tasks_with_indices(self) -> list[tuple[int, Task]]:
        return [
            (index, task)
            for index, task in enumerate(self._tasks, start=1)
            if not task.completed
        ]

    def load_tasks(self, tasks: List[Task]) -> None:
        self._tasks = tasks.copy()

    def update_task(
        self,
        index: int,
        title: str | None = None,
        description: str | None = None,
        completed: bool | None = None,
    ) -> Task:
        task = self._tasks[index]

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if completed is not None:
            task.completed = completed

        return task

    def search_tasks(self, keyword: str) -> List[Task]:
        keyword = keyword.lower()
        return [
            task
            for task in self._tasks
            if keyword in task.title.lower() or keyword in task.description.lower()
        ]

    def search_tasks_with_indices(self, keyword: str) -> list[tuple[int, Task]]:
        keyword = keyword.lower()
        return [
            (index, task)
            for index, task in enumerate(self._tasks, start=1)
            if keyword in task.title.lower() or keyword in task.description.lower()
        ]
