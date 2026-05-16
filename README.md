# tasktracker

A simple Python task tracker with both a command-line interface and a Python REPL interface.

## Features

- Add, update, remove, and complete tasks
- List all tasks
- Filter pending tasks
- Search tasks
- Use different task JSON files
- Save the active task file in a config file
- Optionally override the task data directory
- Works from the CLI and from Python/IDLE repl

---

## Project Layout

```text
tasktracker_pkg/
├── pyproject.toml
├── README.md
├── src/
│   └── tasktracker/
│       ├── __init__.py
│       ├── __main__.py
│       ├── .config.json
│       ├── cli.py
│       ├── manager.py
│       ├── models.py
│       ├── repl.py
│       ├── storage.py
│       └── task_data/
│           └── tasks.json
└── tests/
```

## Clone the repository

```bash
git clone https://github.com/jordankendall86/tasktracker_pkg
```

## Example script

```python
from tasktracker import TaskManager

manager = TaskManager()
manager.add_task("Write docs")
manager.complete_task(0)

for task in manager.list_tasks():
    print(task)
```

## Example repl
```Option 1:
from tasktracker.repl import start_repl
start_repl()

Option 2:
from tasktracker import tasktracker
tasktracker()
```

## Commands
```Command to run all tests (without listing) from any path
python -m unittest discover -s tests

Command to run all tests listing each test done from any path
python -m unittest discover -s tests -v

Command to run all tests listing each from root package folder (tasktracker_pkg)
python -m tests

Command to run all tests from one directory up from root package folder (tasktracker_pkg)
python -m tasktracker_pkg.tests

Command to run specific tests when in tests folder
python -m unittest test_tasktracker.py
python -m unittest test_repl.py

Command to run specific tests when at root package folder (tasktracker_pkg)
python -m unittest tests.test_tasktracker
python -m unittest tests.test_repl

Example task_data_path_override input in .config.json:
"C:\\Users\\p3051624\\OneDrive - Charter Communications\\Documents\\Python\\tasktracker_pkg\\tests\\task_data"
```

## Developer Notes

For developer-focused setup, architecture, packaging, and testing details, see [DEVELOPMENT.md](DEVELOPMENT.md).

