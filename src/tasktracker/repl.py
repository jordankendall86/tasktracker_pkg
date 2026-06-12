from pathlib import Path
import os
import shlex

from colorama import Fore

from .cli import main, color_text

def run_cmd(command: str) -> None:
    argv = shlex.split(command)
    main(argv)


def start_repl() -> None:
    print("tasktracker interactive mode")
    print("Type 'help' for help, 'current' to show path, 'setpath <path>' to change path, or 'exit' to quit.")

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

        if not command:
            continue

        try:
            run_cmd(command)
        except SystemExit:
            pass


def tasktracker() -> None:
    start_repl()