from pathlib import Path
import os
import shlex

from colorama import Fore

from .cli import main, color_text

def run_cmd(command: str) -> None:
    """
    Run a tasktracker CLI command from a Python REPL.

    Examples:
        run_cmd("list")
        run_cmd('add "Write report" -d "Quarterly report"')
        run_cmd("pending")
        run_cmd(r"setpath C:\\Users\\name\\Documents\\task_data")
    """
    argv = shlex.split(command)
    main(argv)


def start_repl() -> None:
    print("tasktracker interactive mode")
    print(f"Current working directory: {Path.cwd()}")
    print("Environment variable TASKTRACKER_HOME will be used if set in .env.")
    print("Type 'help' for help, 'pwd' to show folder, 'cd <path>' to change folder, or 'exit' to quit.")

    while True:
        try:
            command = input("tasktracker> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if command in {"exit", "quit"}:
            break

        if command == "help":
            run_cmd("")
            continue

        if command == "pwd":
            print(Path.cwd())
            continue

        if command.startswith("cd "):
            new_dir = command[3:].strip()
            try:
                os.chdir(new_dir)
                print(f"Changed directory to: {Path.cwd()}")
            except FileNotFoundError:
                print(f"{color_text("Error:", Fore.RED)} directory does not exist: {new_dir}")
            continue

        if not command:
            continue

        try:
            run_cmd(command)
        except SystemExit:
            pass


def tasktracker() -> None:
    start_repl()