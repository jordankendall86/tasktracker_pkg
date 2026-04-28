# tasktracker

`tasktracker` is a small Python task-tracking application with:

- a command-line interface
- a Python interactive prompt
- JSON-backed task storage
- a package-local configuration file
- optional override support for the task data directory

This is written for developers working on the codebase.
For general usage and project overview, see [README.md](README.md).

---

## Contents

- [Overview](#overview)
- [Project Layout](#project-layout)
- [Architecture Notes](#architecture-notes)
- [Configuration Model](#configuration-model)
- [CLI Commands](#cli-commands)
- [Interactive Prompt Usage](#interactive-prompt-usage)
- [Using tasktracker in Python Scripts](#using-tasktracker-in-python-scripts)
- [Packaging](#packaging)
- [Testing](#testing)
- [Development Workflow](#development-workflow)
- [Path Resolution Rules](#path-resolution-rules)
- [Example Config](#example-config)
- [Example Developer Session](#example-developer-session)

---

## Overview

The application stores tasks in JSON files and exposes operations such as:

- add
- list
- update
- complete
- remove
- pending
- search
- files
- current
- use
- setpath

Instead, runtime behavior is driven by:

- package-relative paths
- `.config.json`
- optional `task_data_path_override`

---

## Project Layout

~~~text
tasktracker_pkg/
├── pyproject.toml
├── README.md
├── src/
│   └── tasktracker/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── manager.py
│       ├── models.py
│       ├── repl.py
│       ├── storage.py
│       ├── .config.json
│       └── task_data/
│           └── tasks.json
└── tests/
    ├── __main__.py
    ├── test_repl.py
    └── test_tasktracker.py
~~~

### Important runtime files

#### Package config file
~~~text
src/tasktracker/.config.json
~~~

#### Default task data directory
~~~text
src/tasktracker/task_data/
~~~

When installed locally, these move under the installed package directory in `site-packages`.

---

## Architecture Notes

## Core design

The application is centered around a CLI layer in `cli.py`, an interactive prompt in `repl.py`, and core task logic separated into supporting modules.

### Main architectural components

#### `cli.py`
Responsible for:
- argument parsing
- CLI subcommands
- config access
- task file resolution
- command dispatch

#### `repl.py`
Responsible for:
- starting the interactive prompt
- accepting commands in a loop
- passing those commands into the CLI command flow

#### `manager.py`
Responsible for:
- task-management operations
- coordinating task updates
- applying business logic to loaded task collections

#### `models.py`
Responsible for:
- task data structures
- task model representation
- conversions between Python objects and JSON-friendly data

#### `storage.py`
Responsible for:
- reading task JSON files
- writing task JSON files
- persistence behavior

### Main architectural decisions

#### 1. Config is package-relative
The config file location is fixed relative to the installed module:

~~~python
Path(__file__).resolve().parent / ".config.json"
~~~

This avoids circular path resolution.

#### 2. Task data location is configurable
Task data normally lives under:

~~~text
<module_dir>/task_data
~~~

but may be overridden by:

~~~json
"task_data_path_override"
~~~

stored in `.config.json`.

#### 3. Invalid overrides fall back safely
If `task_data_path_override` is missing, invalid, or points to a non-existent path, the app falls back to the default package `task_data` directory.

#### 4. Active file is config-driven
The active task JSON filename is stored in `.config.json` using:

~~~json
"active_file"
~~~

This keeps file-selection state outside the code and outside environment variables.

---

## Configuration Model

The application uses a single config file:

~~~text
.config.json
~~~

The file stores:

- `active_file`
- `task_data_path_override`

### Config keys

#### `active_file`
The default task JSON file used by commands unless overridden temporarily with `--file`.

#### `task_data_path_override`
Optional absolute or resolvable path to a directory containing task JSON files.

If valid, that directory is used.

If invalid, tasktracker falls back to:

~~~text
<module_dir>/task_data
~~~

---

## CLI Commands

### Core task commands

~~~bash
tasktracker add "Write report" -d "Quarterly report"
tasktracker list
tasktracker update 1 --title "Write final report"
tasktracker complete 1
tasktracker remove 1
tasktracker pending
tasktracker search report
~~~

### File-selection and path commands

#### Show current runtime state
~~~bash
tasktracker current
~~~

#### Show available JSON files
~~~bash
tasktracker files
~~~

#### Set the active JSON file
~~~bash
tasktracker use work.json
~~~

#### Temporarily override the file for one command
~~~bash
tasktracker list --file work.json
~~~

#### Save a task-data directory override
~~~bash
tasktracker setpath C:\Users\your_username\Documents\custom_task_data
~~~

`setpath` writes the selected directory to `.config.json` as:

~~~json
{
  "task_data_path_override": "C:\\Users\\your_username\\Documents\\custom_task_data"
}
~~~

The command validates that the directory exists before saving it.

---

## Interactive Prompt Usage

The package provides an interactive prompt for Python or IDLE usage.

### Start the interactive prompt

~~~python
from tasktracker import tasktracker
tasktracker()
~~~

You can then enter commands interactively, one at a time.

### Example interactive session

~~~text
>>> from tasktracker import tasktracker
>>> tasktracker()
tasktracker> current
tasktracker> add "Write report" -d "Quarterly report"
tasktracker> list
tasktracker> pending
tasktracker> use work.json
tasktracker> files
tasktracker> setpath "C:\Users\your_username\Documents\custom_task_data"
tasktracker> current
tasktracker> exit
~~~

### Windows path note

When entering a Windows path at the interactive prompt, quote the directory path, especially if it contains spaces:

~~~text
tasktracker> setpath "C:\Users\your_username\Documents\custom_task_data"
~~~

This helps ensure the path is parsed correctly by the interactive command parser.

---

## Using tasktracker in Python Scripts

In addition to CLI and interactive prompt usage, you can use tasktracker as a Python library in your own scripts.

### Example: start the interactive prompt from a script

Create a file such as `launch_tasktracker.py`:

~~~python
from tasktracker import tasktracker

tasktracker()
~~~

Run it with:

~~~bash
python launch_tasktracker.py
~~~

This starts the same interactive prompt you would use from Python or IDLE.

---

### Example: use the task model and manager classes directly

Create a script such as `example_tasks.py`:

~~~python
from pathlib import Path

from tasktracker.manager import TaskManager
from tasktracker.models import Task
from tasktracker.storage import JsonStorage

task_file = Path("example_tasks.json")

storage = JsonStorage(task_file)
manager = TaskManager(storage)

manager.add_task("Write report", "Quarterly report")
manager.add_task("Review budget", "Prepare finance notes")

tasks = manager.list_tasks()

for index, task in enumerate(tasks, start=1):
    print(f"{index}. [{task.status}] {task.title} - {task.description}")
~~~

Run it with:

~~~bash
python example_tasks.py
~~~

### Example: complete a task in a script

~~~python
from pathlib import Path

from tasktracker.manager import TaskManager
from tasktracker.storage import JsonStorage

task_file = Path("example_tasks.json")

storage = JsonStorage(task_file)
manager = TaskManager(storage)

manager.complete_task(1)

for index, task in enumerate(manager.list_tasks(), start=1):
    print(f"{index}. [{task.status}] {task.title}")
~~~

### Example: build a custom script around package storage

~~~python
from tasktracker.cli import get_task_data_dir, get_saved_active_file, resolve_task_file_path
from tasktracker.manager import TaskManager
from tasktracker.storage import JsonStorage

task_file = resolve_task_file_path(None)

storage = JsonStorage(task_file)
manager = TaskManager(storage)

print("Task data directory:", get_task_data_dir())
print("Active file:", get_saved_active_file())

for index, task in enumerate(manager.list_tasks(), start=1):
    print(f"{index}. [{task.status}] {task.title}")
~~~

### Notes for script usage

When using tasktracker from custom Python scripts:

- `JsonStorage` handles file persistence
- `TaskManager` handles task operations
- `Task` represents individual task objects
- `cli.py` contains helper functions for resolving configured paths and active files

If you write scripts that depend on the configured active file or configured task-data location, prefer using the helper functions from `cli.py` rather than hard-coding paths.

---

## Packaging

## Build system

The project uses modern Python packaging via `pyproject.toml`.

Typical editable install:

~~~bash
pip install -e .
~~~

Example install to a specific Python on Windows:

~~~bash
py -3.14 -m pip install -e .
~~~

## Package data

The package includes non-code runtime files such as:

- `.config.json`
- `task_data/*.json`

These should be included through your packaging configuration, such as:

- `MANIFEST.in`
- `tool.setuptools.package-data`
- `include-package-data = true`

### Important packaging behavior

When installed locally, the package directory will typically live under:

~~~text
C:\Users\<username>\AppData\Local\Programs\Python\Python314\Lib\site-packages\tasktracker
~~~

That means the installed defaults become:

#### Installed config file
~~~text
...\Lib\site-packages\tasktracker\.config.json
~~~

#### Installed default task-data directory
~~~text
...\Lib\site-packages\tasktracker\task_data
~~~

Unless overridden with `setpath`, runtime data resolution uses those installed-package-relative paths.

---

## Testing

The test suite currently uses `unittest`.

### Run all tests

From the project root:

~~~bash
python -m unittest discover -s tests -v
~~~

## Test structure

### `tests/test_tasktracker.py`
Covers:
- CLI commands
- task file behavior
- active-file behavior
- path validation
- task-data override behavior

### `tests/test_repl.py`
Covers:
- interactive prompt command routing
- CLI command execution from the prompt
- path-sensitive prompt commands such as `setpath`

## Test design notes

The tests rely heavily on:
- temporary directories
- patching path helpers such as:
  - `get_module_dir()`
  - `get_config_file()`
  - `get_task_data_dir()`

For tests that validate the real behavior of `get_task_data_dir()`, the base patch on that function is intentionally stopped in the specialized override test class.

---

## Development Workflow

Recommended workflow:

### 1. Install editable
~~~bash
pip install -e .
~~~

### 2. Run tests often
~~~bash
python -m unittest discover -s tests -v
~~~

### 3. Manually verify key flows
Examples:

~~~bash
tasktracker current
tasktracker files
tasktracker add "Sample task"
tasktracker list
tasktracker setpath C:\some\existing\folder
tasktracker current
~~~

### 4. Verify Python interactive prompt behavior
~~~python
from tasktracker import tasktracker
tasktracker()
~~~

Then try commands such as:

~~~text
tasktracker> current
tasktracker> add "Sample task"
tasktracker> list
tasktracker> exit
~~~

### 5. Verify library/script usage
Create and run a small script that imports:
- `TaskManager`
- `Task`
- `JsonStorage`

and confirms your storage and model behavior still work outside the CLI.

---

## Path Resolution Rules

This is the current path-resolution model.

### Module directory
Resolved from the installed/source package location:

~~~python
Path(__file__).resolve().parent
~~~

### Config file
Always:

~~~python
get_module_dir() / ".config.json"
~~~

### Task data directory
Resolution order:

#### 1. Use `task_data_path_override` if:
- present in `.config.json`
- valid
- exists

#### 2. Otherwise fall back to:
~~~python
get_module_dir() / "task_data"
~~~

### Active task file
Resolution order:

#### 1. CLI `--file` override, if provided
#### 2. saved `active_file` from `.config.json`
#### 3. default filename in code

### Task file path
If the chosen file path is:
- absolute: use it directly
- relative: resolve it under the effective task data directory

---

## Example Config

### Minimal config
~~~json
{
  "active_file": "tasks.json"
}
~~~

### Config with task data override
~~~json
{
  "active_file": "work.json",
  "task_data_path_override": "C:\\Users\\your_username\\Documents\\custom_task_data"
}
~~~

---

## Example Developer Session

### CLI
~~~bash
tasktracker current
tasktracker add "Write report" -d "Quarterly report"
tasktracker list
tasktracker use work.json
tasktracker setpath C:\Users\your_username\Documents\custom_task_data
tasktracker current
tasktracker files
~~~

### Python interactive prompt
~~~python
from tasktracker import tasktracker
tasktracker()
~~~

Then:

~~~text
tasktracker> current
tasktracker> add "Write report" -d "Quarterly report"
tasktracker> list
tasktracker> setpath "C:\Users\your_username\Documents\custom_task_data"
tasktracker> current
tasktracker> exit
~~~

### Python script usage
~~~python
from pathlib import Path

from tasktracker.manager import TaskManager
from tasktracker.storage import JsonStorage

task_file = Path("my_tasks.json")
storage = JsonStorage(task_file)
manager = TaskManager(storage)

manager.add_task("Write report", "Quarterly report")

for index, task in enumerate(manager.list_tasks(), start=1):
    print(f"{index}. [{task.status}] {task.title} - {task.description}")
~~~