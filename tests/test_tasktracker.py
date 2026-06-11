import io
import json
import unittest
import shutil
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tasktracker import TaskManager, Task, JsonStorage
from tasktracker import cli


class TestTaskManager(unittest.TestCase):
    def setUp(self):
        cli.USE_COLOR = False
        self.addCleanup(lambda: setattr(cli, "USE_COLOR", True))
        self.manager = TaskManager()

    def test_add_task(self):
        task = self.manager.add_task("Test task", "Test description")
        self.assertEqual(task.title, "Test task")
        self.assertEqual(task.description, "Test description")
        self.assertFalse(task.completed)

    def test_list_tasks(self):
        self.manager.add_task("Task 1")
        self.manager.add_task("Task 2")
        tasks = self.manager.list_tasks()

        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].title, "Task 1")
        self.assertEqual(tasks[1].title, "Task 2")

    def test_complete_task(self):
        self.manager.add_task("Task 1")
        task = self.manager.complete_task(0)

        self.assertTrue(task.completed)

    def test_remove_task(self):
        self.manager.add_task("Task 1")
        self.manager.add_task("Task 2")

        removed = self.manager.remove_task(0)
        tasks = self.manager.list_tasks()

        self.assertEqual(removed.title, "Task 1")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Task 2")

    def test_get_pending_tasks(self):
        self.manager.add_task("Task 1")
        self.manager.add_task("Task 2")
        self.manager.complete_task(0)

        pending = self.manager.get_pending_tasks()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].title, "Task 2")

    def test_update_task_title(self):
        self.manager.add_task("Old title", "Old description")
        updated = self.manager.update_task(0, title="New title")

        self.assertEqual(updated.title, "New title")
        self.assertEqual(updated.description, "Old description")

    def test_update_task_description(self):
        self.manager.add_task("Task", "Old description")
        updated = self.manager.update_task(0, description="New description")

        self.assertEqual(updated.title, "Task")
        self.assertEqual(updated.description, "New description")

    def test_update_task_completed_true(self):
        self.manager.add_task("Task")
        updated = self.manager.update_task(0, completed=True)

        self.assertTrue(updated.completed)

    def test_update_task_completed_false(self):
        self.manager.add_task("Task")
        self.manager.complete_task(0)
        updated = self.manager.update_task(0, completed=False)

        self.assertFalse(updated.completed)

    def test_search_tasks(self):
        self.manager.add_task("Write report", "Quarterly report")
        self.manager.add_task("Review budget", "Finance planning")

        results = self.manager.search_tasks("report")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Write report")

    def test_search_tasks_case_insensitive(self):
        self.manager.add_task("Write Report", "Quarterly report")

        results = self.manager.search_tasks("report")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Write Report")

    def test_search_tasks_with_indices(self):
        self.manager.add_task("Task A")
        self.manager.add_task("Write report")
        self.manager.add_task("Task C")

        results = self.manager.search_tasks_with_indices("report")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 2)
        self.assertEqual(results[0][1].title, "Write report")

    def test_get_pending_tasks_with_indices(self):
        self.manager.add_task("Task A")
        self.manager.add_task("Task B")
        self.manager.add_task("Task C")
        self.manager.complete_task(0)
        self.manager.complete_task(2)

        pending = self.manager.get_pending_tasks_with_indices()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0][0], 2)
        self.assertEqual(pending[0][1].title, "Task B")

    def test_complete_task_invalid_index_raises(self):
        with self.assertRaises(IndexError):
            self.manager.complete_task(0)

    def test_remove_task_invalid_index_raises(self):
        with self.assertRaises(IndexError):
            self.manager.remove_task(0)

    def test_update_task_invalid_index_raises(self):
        with self.assertRaises(IndexError):
            self.manager.update_task(0, title="No task")


class TestTaskModel(unittest.TestCase):
    def test_task_to_dict_and_from_dict(self):
        task = Task(title="Task 1", description="Desc", completed=True)
        data = task.to_dict()

        self.assertEqual(
            data,
            {"title": "Task 1", "description": "Desc", "completed": True},
        )

        restored = Task.from_dict(data)
        self.assertEqual(restored.title, "Task 1")
        self.assertEqual(restored.description, "Desc")
        self.assertTrue(restored.completed)

    def test_mark_complete(self):
        task = Task(title="Task 1")
        task.mark_complete()
        self.assertTrue(task.completed)


class TestJsonStorage(unittest.TestCase):
    def test_save_and_load_tasks(self):
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "tasks.json"
            storage = JsonStorage(str(file_path))

            tasks = [
                Task("Task 1", "Desc 1", False),
                Task("Task 2", "Desc 2", True),
            ]
            storage.save(tasks)

            loaded = storage.load()
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0].title, "Task 1")
            self.assertFalse(loaded[0].completed)
            self.assertEqual(loaded[1].title, "Task 2")
            self.assertTrue(loaded[1].completed)

    def test_load_missing_file_returns_empty_list(self):
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "missing.json"
            storage = JsonStorage(str(file_path))

            loaded = storage.load()
            self.assertEqual(loaded, [])


class TaskTrackerCliBase(unittest.TestCase):
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

        self.get_task_data_dir_patcher = patch.object(
            cli, "get_task_data_dir", return_value=self.task_data_dir
        )
        self.get_module_dir_patcher = patch.object(
            cli, "get_module_dir", return_value=self.module_dir
        )
        self.get_config_file_patcher = patch.object(
            cli, "get_config_file", return_value=self.config_file
        )

        self._patchers = [
            self.get_task_data_dir_patcher,
            self.get_module_dir_patcher,
            self.get_config_file_patcher,
        ]

        for p in self._patchers:
            p.start()
            self.addCleanup(p.stop)

    def run_cli(self, argv):
        output = io.StringIO()
        with redirect_stdout(output):
            try:
                cli.main(argv)
            except SystemExit:
                pass
        return output.getvalue()

    def read_task_file(self, name="tasks.json"):
        path = self.task_data_dir / name
        return json.loads(path.read_text(encoding="utf-8"))

    def write_task_file(self, name, data):
        path = self.task_data_dir / name
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def read_config(self):
        if not self.config_file.exists():
            return {}
        return json.loads(self.config_file.read_text(encoding="utf-8"))


class TestCliCore(TaskTrackerCliBase):
    def test_help_shown_when_no_command(self):
        output = self.run_cli([])
        self.assertIn("usage:", output)
        self.assertIn("tasktracker", output)

    def test_add_creates_default_task_file_in_task_data(self):
        output = self.run_cli(["add", "Write report", "-d", "Quarterly report"])

        self.assertIn("Added task: Write report", output)
        self.assertTrue((self.task_data_dir / "tasks.json").exists())

        data = self.read_task_file("tasks.json")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Write report")
        self.assertEqual(data[0]["description"], "Quarterly report")
        self.assertFalse(data[0]["completed"])

    def test_list_displays_tasks(self):
        self.write_task_file(
            "tasks.json",
            [
                {"title": "Task 1", "description": "Desc 1", "completed": False},
                {"title": "Task 2", "description": "Desc 2", "completed": True},
            ],
        )

        output = self.run_cli(["list"])
        self.assertIn("Using file:", output)
        self.assertIn("tasks.json", output)
        self.assertIn("1.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Task 1", output)
        self.assertIn("Desc 1", output)
        self.assertIn("2.", output)
        self.assertIn("[Done]", output)
        self.assertIn("Task 2", output)
        self.assertIn("Desc 2", output)

    def test_list_no_tasks(self):
        output = self.run_cli(["list"])
        self.assertIn("No tasks found.", output)

    def test_complete_task(self):
        self.write_task_file(
            "tasks.json",
            [{"title": "Task 1", "description": "", "completed": False}],
        )

        output = self.run_cli(["complete", "1"])
        self.assertIn("Completed task: Task 1", output)

        data = self.read_task_file("tasks.json")
        self.assertTrue(data[0]["completed"])

    def test_complete_invalid_task_number(self):
        output = self.run_cli(["complete", "1"])
        self.assertIn("Error: invalid task number.", output)

    def test_remove_task(self):
        self.write_task_file(
            "tasks.json",
            [
                {"title": "Task 1", "description": "", "completed": False},
                {"title": "Task 2", "description": "", "completed": False},
            ],
        )

        output = self.run_cli(["remove", "1"])
        self.assertIn("Removed task: Task 1", output)

        data = self.read_task_file("tasks.json")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Task 2")

    def test_remove_invalid_task_number(self):
        output = self.run_cli(["remove", "1"])
        self.assertIn("Error: invalid task number.", output)

    def test_update_title_description_and_done(self):
        self.write_task_file(
            "tasks.json",
            [{"title": "Old", "description": "Old desc", "completed": False}],
        )

        output = self.run_cli(
            ["update", "1", "--title", "New", "--description", "New desc", "--done"]
        )

        self.assertIn("Updated task: New", output)
        data = self.read_task_file("tasks.json")
        self.assertEqual(data[0]["title"], "New")
        self.assertEqual(data[0]["description"], "New desc")
        self.assertTrue(data[0]["completed"])

    def test_update_mark_pending(self):
        self.write_task_file(
            "tasks.json",
            [{"title": "Task 1", "description": "", "completed": True}],
        )

        output = self.run_cli(["update", "1", "--pending"])
        self.assertIn("Updated task: Task 1", output)

        data = self.read_task_file("tasks.json")
        self.assertFalse(data[0]["completed"])

    def test_update_invalid_task_number(self):
        output = self.run_cli(["update", "1", "--done"])
        self.assertIn("Error: invalid task number.", output)

    def test_list_uses_task_data_path(self):
        self.write_task_file(
            "moretasks.json",
            [{"title": "Task 1", "description": "", "completed": False}],
        )
        self.run_cli(["use", "moretasks.json"])

        output = self.run_cli(["list"])
        self.assertIn("Using file:", output)
        self.assertIn("moretasks.json", output)
        self.assertIn("1.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Task 1", output)


class TestCliFilteredViews(TaskTrackerCliBase):
    def setUp(self):
        super().setUp()
        self.write_task_file(
            "tasks.json",
            [
                {"title": "Task A", "description": "", "completed": True},
                {"title": "Write report", "description": "Quarterly report", "completed": False},
                {"title": "Task C", "description": "", "completed": True},
                {"title": "Review report", "description": "Draft review", "completed": False},
            ],
        )

    def test_pending_shows_original_indices(self):
        output = self.run_cli(["pending"])
        self.assertIn("Pending Tasks", output)
        self.assertIn("Using file:", output)
        self.assertIn("tasks.json", output)
        self.assertIn("2.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Write report", output)
        self.assertIn("Quarterly report", output)
        self.assertIn("4.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Review report", output)
        self.assertIn("Draft review", output)
        self.assertNotIn("1. [Pending] Write report", output)

    def test_search_shows_original_indices(self):
        output = self.run_cli(["search", "report"])
        self.assertIn("Search Results", output)
        self.assertIn("Using file:", output)
        self.assertIn("tasks.json", output)
        self.assertIn("2.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Write report", output)
        self.assertIn("Quarterly report", output)
        self.assertIn("4.", output)
        self.assertIn("[Pending]", output)
        self.assertIn("Review report", output)
        self.assertIn("Draft review", output)
        self.assertNotIn("1. [Pending] Write report", output)

    def test_pending_no_results(self):
        self.write_task_file(
            "tasks.json",
            [
                {"title": "Task A", "description": "", "completed": True},
                {"title": "Task B", "description": "", "completed": True},
            ],
        )
        output = self.run_cli(["pending"])
        self.assertIn("Pending Tasks", output)
        self.assertIn("Using file:", output)
        self.assertIn("tasks.json", output)
        self.assertIn("No pending tasks found.", output)

    def test_search_no_results(self):
        output = self.run_cli(["search", "nonexistent"])
        self.assertIn("Search Results", output)
        self.assertIn("Using file:", output)
        self.assertIn("tasks.json", output)
        self.assertIn("No matching tasks found.", output)


class TestCliActiveFileBehavior(TaskTrackerCliBase):
    def test_use_sets_active_file_when_file_exists(self):
        self.write_task_file("mytasks.json", [])

        output = self.run_cli(["use", "mytasks.json"])

        self.assertIn("Saved active task file: mytasks.json", output)
        self.assertTrue((self.task_data_dir / "mytasks.json").exists())

        config = self.read_config()
        self.assertEqual(config["active_file"], "mytasks.json")

    def test_current_shows_saved_active_file(self):
        self.write_task_file("mytasks.json", [])
        self.run_cli(["use", "mytasks.json"])
        output = self.run_cli(["current"])

        self.assertIn("Saved active task file: mytasks.json", output)
        self.assertIn("Using file: mytasks.json", output)

    def test_add_uses_saved_active_file(self):
        self.write_task_file("mytasks.json", [])
        self.run_cli(["use", "mytasks.json"])
        self.run_cli(["add", "Task 1"])

        self.assertTrue((self.task_data_dir / "mytasks.json").exists())
        data = self.read_task_file("mytasks.json")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Task 1")

    def test_file_override_only_applies_to_one_command(self):
        self.write_task_file("mytasks.json", [])
        self.run_cli(["use", "mytasks.json"])
        self.run_cli(["--file", "other.json", "add", "Temp Task"])

        self.assertTrue((self.task_data_dir / "other.json").exists())
        self.assertTrue((self.task_data_dir / "mytasks.json").exists())

        config = self.read_config()
        self.assertEqual(config["active_file"], "mytasks.json")

    def test_files_lists_json_files_from_task_data(self):
        self.write_task_file("mytasks.json", [])
        self.run_cli(["use", "mytasks.json"])
        self.run_cli(["add", "Task A"])
        self.run_cli(["--file", "other.json", "add", "Task B"])

        output = self.run_cli(["files"])
        self.assertIn("mytasks.json", output)
        self.assertIn("other.json", output)
        self.assertIn("saved-active", output)

    def test_use_rejects_non_json_file(self):
        output = self.run_cli(["use", "not_json.txt"])
        self.assertIn("Error: active file must be a .json file.", output)

    def test_current_with_file_override_shows_override(self):
        self.write_task_file("mytasks.json", [])
        self.run_cli(["use", "mytasks.json"])
        output = self.run_cli(["--file", "other.json", "current"])

        self.assertIn("Saved active task file: mytasks.json", output)
        self.assertIn("Using file: other.json", output)

    def test_files_uses_task_data_dir_by_default(self):
        self.write_task_file(
            "moretasks.json",
            [{"title": "Task 1", "description": "", "completed": False}],
        )

        output = self.run_cli(["files"])
        self.assertIn(f"JSON files in {self.task_data_dir}", output)
        self.assertIn("moretasks.json", output)


class TestCliHelp(TaskTrackerCliBase):
    def test_main_help_lists_subcommands(self):
        output = self.run_cli(["-h"])
        self.assertIn("add", output)
        self.assertIn("list", output)
        self.assertIn("complete", output)
        self.assertIn("remove", output)
        self.assertIn("pending", output)
        self.assertIn("search", output)
        self.assertIn("update", output)
        self.assertIn("files", output)
        self.assertIn("use", output)
        self.assertIn("current", output)

    def test_list_help_shows_description(self):
        output = self.run_cli(["list", "-h"])
        self.assertIn("List all tasks", output)

    def test_add_help_shows_description(self):
        output = self.run_cli(["add", "-h"])
        self.assertIn("Add a new task", output)


class TestCliPathValidation(TaskTrackerCliBase):
    def test_list_errors_when_task_data_dir_missing(self):
        self.task_data_dir.rmdir()

        output = self.run_cli(["list"])
        self.assertIn("Error:", output)
        self.assertIn("Task data directory does not exist", output)

    def test_files_errors_when_task_data_dir_missing(self):
        self.task_data_dir.rmdir()

        output = self.run_cli(["files"])
        self.assertIn("Error:", output)
        self.assertIn("Task data directory does not exist", output)

    def test_use_errors_when_target_file_does_not_exist(self):
        output = self.run_cli(["use", "missing.json"])
        self.assertIn("Error: file does not exist at path:", output)

    def test_current_errors_when_task_data_dir_missing(self):
        shutil.rmtree(self.module_dir)

        output = self.run_cli(["current"])
        self.assertIn("Error:", output)
        self.assertIn("Tasktracker module directory does not exist", output)


class TestCliTaskDataPathOverride(TaskTrackerCliBase):
    def setUp(self):
        super().setUp()

        # Use the real get_task_data_dir() implementation in this class.
        self.get_task_data_dir_patcher.stop()

    def test_get_task_data_dir_uses_task_data_path_override(self):
        override_dir = self.project_dir / "custom_task_data"
        override_dir.mkdir()

        self.config_file.write_text(
            json.dumps(
                {
                    "active_file": "tasks.json",
                    "task_data_path_override": str(override_dir),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        self.assertEqual(cli.get_task_data_dir(), override_dir.resolve())

    def test_get_task_data_dir_defaults_to_module_task_data(self):
        self.config_file.write_text(
            json.dumps(
                {
                    "active_file": "tasks.json",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        self.assertEqual(
            cli.get_task_data_dir(),
            (self.module_dir / "task_data").resolve(),
        )

    def test_get_task_data_dir_defaults_when_override_path_is_invalid(self):
        invalid_dir = self.project_dir / "does_not_exist"

        self.config_file.write_text(
            json.dumps(
                {
                    "active_file": "tasks.json",
                    "task_data_path_override": str(invalid_dir),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        self.assertEqual(
            cli.get_task_data_dir(),
            (self.module_dir / "task_data").resolve(),
        )

    def test_setpath_saves_task_data_path_override(self):
        override_dir = self.project_dir / "custom_task_data"
        override_dir.mkdir()

        output = self.run_cli(["setpath", str(override_dir)])

        config = json.loads(self.config_file.read_text(encoding="utf-8"))
        self.assertEqual(
            config["task_data_path_override"],
            str(override_dir.resolve()),
        )
        self.assertIn("Saved task data path override:", output)

    def test_setpath_rejects_missing_directory(self):
        missing_dir = self.project_dir / "missing_task_data"

        output = self.run_cli(["setpath", str(missing_dir)])

        self.assertIn("Error:", output)
        self.assertIn("directory does not exist", output)

        config = self.read_config()
        self.assertNotIn("task_data_path_override", config)

    def test_setpath_preserves_active_file(self):
        self.config_file.write_text(
            json.dumps(
                {
                    "active_file": "work.json",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        override_dir = self.project_dir / "custom_task_data"
        override_dir.mkdir()

        self.run_cli(["setpath", str(override_dir)])

        config = json.loads(self.config_file.read_text(encoding="utf-8"))
        self.assertEqual(config["active_file"], "work.json")
        self.assertEqual(
            config["task_data_path_override"],
            str(override_dir.resolve()),
        )


if __name__ == "__main__":
    unittest.main()