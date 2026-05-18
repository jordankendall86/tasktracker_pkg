import sys
import argparse
import json
import textwrap
from pathlib import Path

from colorama import init, Fore, Style

from .manager import TaskManager
from .storage import JsonStorage

DEFAULT_FILE = "tasks.json"

def set_use_color() -> bool:
    if "idlelib" in sys.modules:
        return False
    else:
        init(autoreset=True)
        return True

USE_COLOR = set_use_color()


def color_text(text: str, color: str) -> str:
    if not USE_COLOR:
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def get_installed_package_dir() -> Path:
    return Path(__file__).resolve().parent


def get_task_data_dir() -> Path:
    override = get_task_data_path_override()

    if override:
        try:
            override_path = Path(override).expanduser().resolve()
            if override_path.exists():
                return override_path
        except OSError:
            pass

    return (get_module_dir() / "task_data").resolve()


def get_module_dir() -> Path:
    return Path(__file__).resolve().parent


def get_config_file() -> Path:
    return get_module_dir() / ".config.json"


def load_config() -> dict:
    config_file = get_config_file()

    if not config_file.exists():
        return {}

    try:
        return json.loads(config_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict) -> None:
    config_file = get_config_file()
    config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_saved_active_file() -> str:
    config = load_config()
    return config.get("active_file", DEFAULT_FILE)


def get_task_data_path_override() -> str | None:
    config = load_config()
    return config.get("task_data_path_override")


def resolve_active_file(cli_file: str | None) -> str:
    if cli_file:
        return cli_file
    return get_saved_active_file()


def resolve_task_file_path(file_name: str | None) -> Path:
    validate_required_paths()

    resolved_name = resolve_active_file(file_name)
    path = Path(resolved_name)

    if path.is_absolute():
        return path

    return get_task_data_dir() / path


def validate_required_paths() -> None:
    module_dir = get_module_dir()
    task_data_dir = get_task_data_dir()

    if not module_dir.exists():
        raise FileNotFoundError(
            f"Tasktracker module directory does not exist: {module_dir}"
        )

    if not task_data_dir.exists():
        raise FileNotFoundError(
            f"Task data directory does not exist: {task_data_dir}"
        )


def validate_task_file_parent(path: Path) -> None:
    if not path.parent.exists():
        raise FileNotFoundError(
            f"Directory does not exist for task file: {path.parent}"
        )


def load_manager(file_path: str | None):
    resolved_name = resolve_active_file(file_path)
    resolved_path = resolve_task_file_path(file_path)

    validate_task_file_parent(resolved_path)

    storage = JsonStorage(str(resolved_path))
    manager = TaskManager()
    manager.load_tasks(storage.load())

    return manager, storage, resolved_name, resolved_path


def save_manager(manager: TaskManager, storage: JsonStorage) -> None:
    storage.save(manager.list_tasks())


def print_tasks(tasks):
    if not tasks:
        print("No tasks found.")
        return

    for i, task in enumerate(tasks, start=1):
        status = color_text('[Done]', Fore.GREEN) if task.completed else color_text('[Pending]', Fore.YELLOW)
        description = f" - {task.description}" if task.description else ""
        print(f"{i}. {status} {task.title}{description}")


def print_indexed_tasks(indexed_tasks):
    if not indexed_tasks:
        print(color_text("No tasks found.", Fore.YELLOW))
        return

    for index, task in indexed_tasks:
        print(format_task_line(index, task))


def print_blank_line() -> None:
    print()


def print_section(title: str, color=Fore.CYAN) -> None:
    print()
    print(color_text(title, color))
    print(color_text("-" * len(title), color))


def print_kv_block(rows: list[tuple[str, str]], color=Fore.WHITE) -> None:
    if not rows:
        return

    width = max(len(label) for label, _ in rows)
    for label, value in rows:
        print(f"{color_text(label.ljust(width), color)}  {value}")


def format_task_line(index: int, task, width: int = 88) -> str:
    raw_status = "[Done]" if task.completed else "[Pending]"
    padded_status = raw_status.ljust(10)

    status = (
        color_text(padded_status, Fore.GREEN)
        if task.completed
        else color_text(padded_status, Fore.YELLOW)
    )

    header = f"{index}. {status} {task.title}"

    if not task.description:
        return header

    wrapped_description = textwrap.fill(
        task.description,
        width=width,
        initial_indent=" " * 4,
        subsequent_indent=" " * 4,
    )

    return f"{header}\n{wrapped_description}"


def cmd_add(args):
    manager, storage, active_file, _ = load_manager(args.file)
    task = manager.add_task(args.title, args.description)
    save_manager(manager, storage)
    print(f"Added task: {task.title}")
    print(f"Using file: {active_file}")


def cmd_list(args):
    manager, _, active_file, resolved_path = load_manager(args.file)

    print_section("Task List", Fore.CYAN)
    print_kv_block(
        [
            ("Using file:", active_file),
            ("Resolved path:", str(resolved_path)),
        ],
        Fore.BLUE,
    )
    print_blank_line()

    tasks = manager.list_tasks()
    if not tasks:
        print(color_text("No tasks found.", Fore.YELLOW))
        print_blank_line()
        return

    for index, task in enumerate(tasks, start=1):
        print(format_task_line(index, task))

    print_blank_line()


def cmd_complete(args):
    manager, storage, active_file, _ = load_manager(args.file)
    try:
        task = manager.complete_task(args.index - 1)
        save_manager(manager, storage)
        print(f"Completed task: {task.title}")
        print(f"Using file: {active_file}")
    except IndexError:
        print(f"{color_text("Error:", Fore.RED)} invalid task number.")


def cmd_remove(args):
    manager, storage, active_file, _ = load_manager(args.file)
    try:
        task = manager.remove_task(args.index - 1)
        save_manager(manager, storage)
        print(f"Removed task: {task.title}")
        print(f"Using file: {active_file}")
    except IndexError:
        print(f"{color_text("Error:", Fore.RED)} invalid task number.")


def cmd_pending(args):
    manager, _, active_file, _ = load_manager(args.file)

    print_section("Pending Tasks", Fore.CYAN)
    print(f"Using file: {active_file}")
    print_blank_line()

    indexed_tasks = manager.get_pending_tasks_with_indices()
    if not indexed_tasks:
        print(color_text("No pending tasks found.", Fore.YELLOW))
        print_blank_line()
        return

    print_indexed_tasks(indexed_tasks)
    print_blank_line()


def cmd_search(args):
    manager, _, active_file, _ = load_manager(args.file)

    print_section("Search Results", Fore.CYAN)
    print(f"Using file: {active_file}")
    print_blank_line()

    indexed_tasks = manager.search_tasks_with_indices(args.keyword)
    if not indexed_tasks:
        print(color_text("No matching tasks found.", Fore.YELLOW))
        print_blank_line()
        return

    print_indexed_tasks(indexed_tasks)
    print_blank_line()


def cmd_update(args):
    manager, storage, active_file, _ = load_manager(args.file)

    try:
        completed = None
        if args.done:
            completed = True
        elif args.pending:
            completed = False

        task = manager.update_task(
            args.index - 1,
            title=args.title,
            description=args.description,
            completed=completed,
        )
        save_manager(manager, storage)
        print(f"Updated task: {task.title}")
        print(f"Using file: {active_file}")
    except IndexError:
        print(f"{color_text("Error:", Fore.RED)} invalid task number.")


def format_file_size(size: int) -> str:
    if size < 1024:
        return f"{size} bytes"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def cmd_files(args):
    validate_required_paths()

    if args.directory:
        directory = Path(args.directory)

        if not directory.is_absolute():
            directory = (get_task_data_dir() / directory).resolve()
        else:
            directory = directory.resolve()
    else:
        directory = get_task_data_dir().resolve()

    if not directory.exists():
        print(f"{color_text('Error:', Fore.RED)} directory does not exist: {directory}")
        return

    json_files = sorted(directory.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in: {directory}")
        return

    saved_active = Path(get_saved_active_file()).name
    effective_active = Path(resolve_active_file(args.file)).name

    print(color_text(f"JSON files in {directory}:", Fore.MAGENTA))
    for i, file_path in enumerate(json_files, start=1):
        markers = []

        if file_path.name == saved_active:
            markers.append("saved-active")

        if file_path.name == effective_active:
            markers.append("in-use")

        marker_text = f" [{','.join(markers)}]" if markers else ""
        size = format_file_size(file_path.stat().st_size)
        print(f"  {i}. {file_path.name:<25} {size:>10}{marker_text}")

    if args.file:
        print(f"\nTemporary override for this command: {args.file}")


def cmd_use(args):
    file_name = args.file_name

    if not file_name.endswith(".json"):
        print(f"{color_text('Error:', Fore.RED)} active file must be a .json file.")
        return

    resolved_path = resolve_task_file_path(file_name)

    if not resolved_path.exists():
        print(f"{color_text('Error:', Fore.RED)} file does not exist at path: {resolved_path}")
        return

    config = load_config()
    config["active_file"] = file_name
    save_config(config)

    print(f"{color_text('Saved active task file:', Fore.CYAN)} {file_name}")
    print(f"{color_text('Resolved path:', Fore.BLUE)} {resolved_path}")


def cmd_current(args):
    try:
        config = load_config()
        saved_file = get_saved_active_file()
        effective_file = resolve_active_file(args.file)
        resolved_path = resolve_task_file_path(args.file)
        task_data_path_override = config.get("task_data_path_override")
        task_data_dir = get_task_data_dir()

        print(f"{color_text('Saved active task file:', Fore.CYAN)} {saved_file}")
        print(f"{color_text('Using file:', Fore.BLUE)} {effective_file}")
        print(f"{color_text('Resolved path:', Fore.BLUE)} {resolved_path}")
        print(f"{color_text('Task data path override:', Fore.MAGENTA)} {task_data_path_override}")
        print(f"{color_text('Task data directory:', Fore.MAGENTA)} {task_data_dir}")

        if task_data_path_override:
            override_path = Path(task_data_path_override).expanduser()
            if not override_path.exists():
                print(f"{color_text('Warning:', Fore.YELLOW)} override path is invalid; using default task_data directory.")

        print(f"{color_text('Config file:', Fore.MAGENTA)} {get_config_file()}")
    except FileNotFoundError as e:
        print(f"{color_text('Error:', Fore.RED)} {e}")


def cmd_setpath(args):
    directory = Path(args.directory).expanduser().resolve()

    if not directory.exists() or not directory.is_dir():
        print(f"{color_text('Error:', Fore.RED)} directory does not exist: {directory}")
        return

    config = load_config()
    config["task_data_path_override"] = str(directory)
    save_config(config)

    print(f"{color_text('Saved task data path override:', Fore.CYAN)} {directory}")
    print(f"{color_text('Task data directory:', Fore.MAGENTA)} {get_task_data_dir()}")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tasktracker",
        description="Task tracker CLI",
        epilog=(
            "Examples:\n"
            "  tasktracker add \"Write report\" -d \"Quarterly report\"\n"
            "  tasktracker list\n"
            "  tasktracker pending\n"
            "  tasktracker search report\n"
            "  tasktracker update 1 --title \"Write final report\"\n"
            "  tasktracker update 1 --description \"Finalize and submit by Friday\"\n"
            "  tasktracker update 1 --done\n"
            "  tasktracker update 1 --pending\n"
            "  tasktracker complete 1\n"
            "  tasktracker remove 2\n"
            "  tasktracker files\n"
            "  tasktracker files --directory ../tests/task_data\n"
            "  tasktracker use work_tasks.json\n"
            "  tasktracker current\n"
            "  tasktracker setpath \"C:\\Users\\<username>\\..\\task_data\"\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--file",
        default=None,
        help="Temporarily use a specific task JSON file for this command",
    )

    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a new task", description="Add a new task")
    add_parser.add_argument("title", help="Task title")
    add_parser.add_argument("-d", "--description", default="", help="Task description")
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser(
        "list",
        help="List all tasks",
        description="List all tasks",
    )
    list_parser.set_defaults(func=cmd_list)

    complete_parser = subparsers.add_parser(
        "complete",
        help="Mark a task complete",
        description="Mark a task complete",
    )
    complete_parser.add_argument("index", type=int, help="Task number from the list output")
    complete_parser.set_defaults(func=cmd_complete)

    remove_parser = subparsers.add_parser(
        "remove",
        help="Remove a task",
        description="Remove a task",
    )
    remove_parser.add_argument("index", type=int, help="Task number from the list output")
    remove_parser.set_defaults(func=cmd_remove)

    pending_parser = subparsers.add_parser(
        "pending",
        help="List only pending tasks", 
        description="List only pending tasks",
    )
    pending_parser.set_defaults(func=cmd_pending)

    search_parser = subparsers.add_parser(
        "search",
        help="Search tasks by keyword",
        description="Search tasks by keyword",
    )
    search_parser.add_argument("keyword", help="Keyword to search for")
    search_parser.set_defaults(func=cmd_search)

    update_parser = subparsers.add_parser("update", help="Update an existing task")
    update_parser.add_argument("index", type=int, help="Task number from the list output")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--description", help="New description")

    status_group = update_parser.add_mutually_exclusive_group()
    status_group.add_argument("--done", action="store_true", help="Mark task as done")
    status_group.add_argument("--pending", action="store_true", help="Mark task as pending")

    update_parser.set_defaults(func=cmd_update)

    use_parser = subparsers.add_parser(
        "use",
        help="Set the saved active JSON task file",
        description="Set the saved active JSON task file",
    )
    use_parser.add_argument("file_name", help="JSON file to save as the active task file")
    use_parser.set_defaults(func=cmd_use)

    current_parser = subparsers.add_parser(
        "current",
        help="Show the saved active JSON task file",
        description="Show the saved active JSON task file",
    )
    current_parser.set_defaults(func=cmd_current)

    files_parser = subparsers.add_parser(
        "files",
        help="List JSON storage files neatly",
        description="List JSON task files from the task_data folder",
    )
    files_parser.add_argument(
        "-d",
        "--directory",
        default=None,
        help="Optional subdirectory or absolute directory to scan for JSON files",
    )
    files_parser.set_defaults(func=cmd_files)

    setpath_parser = subparsers.add_parser(
        "setpath",
        help="set the task data directory override",
        description="Save a task data directory override in .config.json.",
    )
    setpath_parser.add_argument(
        "directory",
        help="directory path to use for task data files",
    )
    setpath_parser.set_defaults(func=cmd_setpath)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return

    try:
        args.func(args)
    except FileNotFoundError as e:
        print(f"{color_text("Error:", Fore.RED)} {e}")