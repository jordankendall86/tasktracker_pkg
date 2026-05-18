import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tasktracker import cli
from tasktracker import repl


class TestRepl(unittest.TestCase):
    def setUp(self):
        cli.USE_COLOR = False
        self.addCleanup(lambda: setattr(cli, "USE_COLOR", True))
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

        self.project_dir = Path(self.tmpdir.name)
        self.module_dir = self.project_dir / "src" / "tasktracker"
        self.module_dir.mkdir(parents=True)

        self.task_data_dir = self.module_dir / "task_data"
        self.task_data_dir.mkdir(parents=True)

        self.config_file = self.module_dir / ".config.json"

        patchers = [
            patch.object(cli, "get_task_data_dir", return_value=self.task_data_dir),
            patch.object(cli, "get_module_dir", return_value=self.module_dir),
            patch.object(cli, "get_config_file", return_value=self.config_file),
        ]

        self._patchers = patchers
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)

    def capture_output(self, func, *args, **kwargs):
        output = io.StringIO()
        with redirect_stdout(output):
            try:
                func(*args, **kwargs)
            except SystemExit:
                pass
        return output.getvalue()

    def test_run_cmd_list_no_tasks(self):
        output = self.capture_output(repl.run_cmd, "list")
        self.assertIn("Task List", output)
        self.assertIn("---------", output)
        self.assertIn("Using file:", output)
        self.assertIn("tasks.json", output)
        self.assertIn("No tasks found.", output)

    def test_run_cmd_add_and_list(self):
        self.capture_output(repl.run_cmd, 'add "Write report" -d "Quarterly report"')
        output = self.capture_output(repl.run_cmd, "list")

        self.assertIn("1.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Write report", output)
        self.assertIn("Quarterly report", output)

    def test_run_cmd_use_and_current(self):
        (self.task_data_dir / "mytasks.json").write_text("[]", encoding="utf-8")

        self.capture_output(repl.run_cmd, "use mytasks.json")
        output = self.capture_output(repl.run_cmd, "current")

        self.assertIn("Saved active task file: mytasks.json", output)
        self.assertIn("Using file: mytasks.json", output)

    def test_run_cmd_files(self):
        (self.task_data_dir / "mytasks.json").write_text("[]", encoding="utf-8")

        self.capture_output(repl.run_cmd, "use mytasks.json")
        self.capture_output(repl.run_cmd, 'add "Task 1"')
        output = self.capture_output(repl.run_cmd, "files")

        self.assertIn("mytasks.json", output)

    def test_run_cmd_pending_preserves_original_index(self):
        tasks = [
            {"title": "Task A", "description": "", "completed": True},
            {"title": "Task B", "description": "", "completed": False},
            {"title": "Task C", "description": "", "completed": True},
            {"title": "Task D", "description": "", "completed": False},
        ]
        (self.task_data_dir / "tasks.json").write_text(
            json.dumps(tasks, indent=2),
            encoding="utf-8",
        )

        output = self.capture_output(repl.run_cmd, "pending")
        self.assertIn("Pending Tasks", output)
        self.assertIn("Using file:", output)
        self.assertIn("tasks.json", output)
        self.assertIn("2.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Task B", output)
        self.assertIn("4.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Task D", output)

    def test_run_cmd_search_preserves_original_index(self):
        tasks = [
            {"title": "Alpha", "description": "", "completed": False},
            {"title": "Write report", "description": "", "completed": False},
            {"title": "Gamma", "description": "", "completed": False},
        ]
        (self.task_data_dir / "tasks.json").write_text(
            json.dumps(tasks, indent=2),
            encoding="utf-8",
        )

        output = self.capture_output(repl.run_cmd, "search report")
        self.assertIn("Search Results", output)
        self.assertIn("Using file:", output)
        self.assertIn("tasks.json", output)
        self.assertIn("2.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Write report", output)

    def test_run_cmd_empty_string_shows_help(self):
        output = self.capture_output(repl.run_cmd, "")
        self.assertIn("usage:", output)

    def test_start_repl_help_and_exit(self):
        inputs = iter(["help", "exit"])

        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            output = self.capture_output(repl.start_repl)

        self.assertIn("tasktracker interactive mode", output)
        self.assertIn("usage:", output)

    def test_run_cmd_list_uses_task_data_dir(self):
        (self.task_data_dir / "moretasks.json").write_text(
            json.dumps(
                [{"title": "Task 1", "description": "", "completed": False}],
                indent=2,
            ),
            encoding="utf-8",
        )

        self.capture_output(repl.run_cmd, "use moretasks.json")
        output = self.capture_output(repl.run_cmd, "list")

        self.assertIn("Using file:", output)
        self.assertIn("moretasks.json", output)
        self.assertIn("1.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Task 1", output)

    def test_run_cmd_files_uses_task_data_dir(self):
        (self.task_data_dir / "moretasks.json").write_text(
            json.dumps(
                [{"title": "Task 1", "description": "", "completed": False}],
                indent=2,
            ),
            encoding="utf-8",
        )

        output = self.capture_output(repl.run_cmd, "files")

        self.assertIn(f"JSON files in {self.task_data_dir}", output)
        self.assertIn("moretasks.json", output)

    def test_repl_imported_functions_still_run_without_path_crash(self):
        output = self.capture_output(repl.run_cmd, "")
        self.assertIn("usage:", output)

    def test_start_repl_pwd_and_exit(self):
        inputs = iter(["pwd", "exit"])

        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            output = self.capture_output(repl.start_repl)

        self.assertIn("Current working directory:", output)

    def test_start_repl_cd_invalid_path(self):
        inputs = iter(["cd does_not_exist", "exit"])

        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            output = self.capture_output(repl.start_repl)

        self.assertIn("Error: directory does not exist:", output)
    
    def test_run_cmd_use_errors_when_file_missing(self):
        output = self.capture_output(repl.run_cmd, "use missing.json")
        self.assertIn("Error: file does not exist at path:", output)

    def test_run_cmd_setpath(self):
        override_dir = self.project_dir / "custom_task_data"
        override_dir.mkdir()

        self.config_file.write_text("{}", encoding="utf-8")

        out = io.StringIO()
        with redirect_stdout(out):
            repl.run_cmd(f'setpath "{override_dir}"')

        output = out.getvalue()
        config = json.loads(self.config_file.read_text(encoding="utf-8"))

        self.assertNotIn("Error:", output)
        self.assertIn("Saved task data path override:", output)
        self.assertIn("task_data_path_override", config)
        self.assertEqual(
            config["task_data_path_override"],
            str(override_dir.resolve()),
        )

    def test_run_cmd_setpath_rejects_missing_directory(self):
        missing_dir = self.project_dir / "missing_task_data"

        self.config_file.write_text("{}", encoding="utf-8")

        out = io.StringIO()
        with redirect_stdout(out):
            repl.run_cmd(f'setpath "{missing_dir}"')

        output = out.getvalue()
        config = json.loads(self.config_file.read_text(encoding="utf-8"))

        self.assertIn("Error:", output)
        self.assertIn("directory does not exist", output)
        self.assertNotIn("task_data_path_override", config)