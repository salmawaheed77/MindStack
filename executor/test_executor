"""Unit tests for the executor package. Run: python3 -m unittest executor.test_executor -v"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import security
from .executor import execute_command, get_supported_actions


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name).resolve()
        self.workspace_patch = patch.object(security, "WORKSPACE", self.workspace)
        self.workspace_patch.start()

    def tearDown(self):
        self.workspace_patch.stop()
        self.temp_dir.cleanup()

    def test_non_object_payload_is_rejected(self):
        result = execute_command(["get_date_time"])
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "validation_error")

    def test_missing_action_is_rejected(self):
        result = execute_command({})
        self.assertEqual(result["error"], "validation_error")

    def test_unknown_action(self):
        result = execute_command({"action": "do_magic"})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "unsupported_action")

    def test_raw_shell_is_rejected(self):
        result = execute_command({"action": "open_application", "target": "firefox", "command": "rm -rf /"})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "permission_denied")

    def test_create_and_read_file(self):
        created = execute_command({"action": "create_file", "path": "notes/hello.txt", "content": "hello"})
        self.assertTrue(created["success"], created)
        read = execute_command({"action": "read_file", "path": "notes/hello.txt"})
        self.assertTrue(read["success"], read)
        self.assertEqual(read["data"], "hello")

    def test_create_file_does_not_overwrite(self):
        (self.workspace / "same.txt").write_text("original", encoding="utf-8")
        result = execute_command({"action": "create_file", "path": "same.txt", "content": "replacement"})
        self.assertEqual(result["error"], "already_exists")
        self.assertEqual((self.workspace / "same.txt").read_text(encoding="utf-8"), "original")

    def test_path_traversal_is_rejected(self):
        result = execute_command({"action": "create_file", "path": "../outside.txt", "content": "no"})
        self.assertEqual(result["error"], "permission_denied")

    def test_symlink_path_is_rejected(self):
        outside = self.workspace.parent / "outside_executor_test.txt"
        outside.write_text("safe", encoding="utf-8")
        link = self.workspace / "link.txt"
        link.symlink_to(outside)
        try:
            result = execute_command({"action": "read_file", "path": "link.txt"})
            self.assertEqual(result["error"], "permission_denied")
        finally:
            outside.unlink(missing_ok=True)

    def test_copy_does_not_overwrite(self):
        (self.workspace / "source.txt").write_text("source", encoding="utf-8")
        (self.workspace / "target.txt").write_text("target", encoding="utf-8")
        result = execute_command({"action": "copy_file", "source": "source.txt", "destination": "target.txt"})
        self.assertEqual(result["error"], "already_exists")
        self.assertEqual((self.workspace / "target.txt").read_text(encoding="utf-8"), "target")

    def test_rename_nested_file(self):
        folder = self.workspace / "class"
        folder.mkdir()
        (folder / "old.txt").write_text("x", encoding="utf-8")
        result = execute_command({"action": "rename_file", "path": "class/old.txt", "new_name": "new.txt"})
        self.assertTrue(result["success"], result)
        self.assertTrue((folder / "new.txt").is_file())

    def test_delete_requires_confirmation(self):
        (self.workspace / "delete.txt").write_text("x", encoding="utf-8")
        result = execute_command({"action": "delete_file", "path": "delete.txt"})
        self.assertEqual(result["error"], "confirmation_required")
        self.assertTrue((self.workspace / "delete.txt").exists())

    def test_delete_with_confirmation(self):
        (self.workspace / "delete.txt").write_text("x", encoding="utf-8")
        result = execute_command({"action": "delete_file", "path": "delete.txt"}, confirmed=True)
        self.assertTrue(result["success"], result)
        self.assertFalse((self.workspace / "delete.txt").exists())

    def test_confirmed_inside_payload_is_ignored(self):
        """The AI model must not be able to approve a deletion by itself."""
        (self.workspace / "keep.txt").write_text("x", encoding="utf-8")
        for flag in ({"confirmed": True}, {"_confirmed": True}):
            payload = {"action": "delete_file", "path": "keep.txt", **flag}
            result = execute_command(payload)
            self.assertEqual(result["error"], "confirmation_required", flag)
            self.assertTrue((self.workspace / "keep.txt").exists())

    def test_confirmed_must_be_exactly_true(self):
        (self.workspace / "keep.txt").write_text("x", encoding="utf-8")
        result = execute_command({"action": "delete_file", "path": "keep.txt"}, confirmed="yes")
        self.assertEqual(result["error"], "confirmation_required")

    def test_payload_is_not_modified(self):
        payload = {"action": "get_date_time"}
        execute_command(payload, confirmed=True)
        self.assertEqual(payload, {"action": "get_date_time"})

    def test_messages_are_speakable(self):
        (self.workspace / "a.txt").write_text("x", encoding="utf-8")
        cases = [
            ({"action": "create_file", "path": "a.txt"}, "already_exists"),
            ({"action": "create_folder", "path": "a.txt"}, "already_exists"),
            ({"action": "read_file", "path": "missing.txt"}, "not_found"),
            ({"action": "list_files", "folder": "a.txt"}, "not_a_directory"),
        ]
        for payload, error in cases:
            result = execute_command(payload)
            self.assertEqual(result["error"], error, payload)
            self.assertNotIn("Errno", result["message"], payload)
            self.assertNotIn(str(self.workspace), result["message"], payload)

    def test_workspace_root_cannot_be_deleted(self):
        result = execute_command({"action": "delete_folder", "path": "."}, confirmed=True)
        self.assertEqual(result["error"], "permission_denied")

    def test_cpu_and_process_actions_are_registered(self):
        actions = get_supported_actions()
        self.assertIn("get_cpu_usage", actions)
        self.assertIn("get_processes", actions)

    def test_get_processes_default_limit_and_memory_sort(self):
        result = execute_command({"action": "get_processes"})
        self.assertTrue(result["success"], result)
        data = result["data"]
        self.assertLessEqual(len(data), 10)
        self.assertIn("memory_percent", data[0])
        memory = [item["memory_percent"] for item in data]
        self.assertEqual(memory, sorted(memory, reverse=True))

    def test_get_processes_custom_limit(self):
        result = execute_command({"action": "get_processes", "limit": 3})
        self.assertLessEqual(len(result["data"]), 3)

    def test_get_processes_rejects_bad_limit(self):
        for bad in (0, 101, "5", True, 2.5):
            result = execute_command({"action": "get_processes", "limit": bad})
            self.assertEqual(result["error"], "validation_error", bad)

    def test_text_editor_falls_back_to_gnome_text_editor(self):
        from . import app_manager

        def fake_which(name):
            return "/usr/bin/gnome-text-editor" if name == "gnome-text-editor" else None

        with patch.object(app_manager.shutil, "which", side_effect=fake_which), \
             patch.object(app_manager.subprocess, "Popen") as popen:
            result = execute_command({"action": "open_application", "target": "text editor"})
        self.assertTrue(result["success"], result)
        self.assertEqual(popen.call_args[0][0], ["/usr/bin/gnome-text-editor"])

    def test_text_editor_not_installed_message(self):
        from . import app_manager
        with patch.object(app_manager.shutil, "which", return_value=None):
            result = execute_command({"action": "open_application", "target": "text_editor"})
        self.assertEqual(result["error"], "application_not_installed")

    def test_empty_folder_means_workspace_root(self):
        (self.workspace / "a.txt").write_text("x", encoding="utf-8")
        for folder in ("", None, "."):
            result = execute_command({"action": "list_files", "folder": folder})
            self.assertTrue(result["success"], (folder, result))
            self.assertEqual([i["name"] for i in result["data"]], ["a.txt"])

    def test_process_names_use_15_char_kernel_limit(self):
        from . import app_manager
        for key, (_exe, proc) in app_manager.APPS.items():
            self.assertLessEqual(len(app_manager._comm(proc)), 15, key)
        self.assertEqual(app_manager._comm("gnome-calculator"), "gnome-calculato")

    def test_shell_capable_apps_are_not_allowed(self):
        for target in ("terminal", "code"):
            result = execute_command({"action": "open_application", "target": target})
            self.assertEqual(result["error"], "validation_error", target)

    def test_power_action_failure_is_reported(self):
        from . import system_manager
        fake = type("P", (), {"returncode": 1,
                              "communicate": lambda self, timeout=None: ("", "Access denied\n")})()
        with patch.object(system_manager.shutil, "which", return_value="/bin/true"), \
             patch.object(system_manager.subprocess, "Popen", return_value=fake):
            result = execute_command({"action": "shutdown_system"}, confirmed=True)
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Access denied")

    def test_list_running_uses_full_names(self):
        from . import app_manager
        fake = type("R", (), {"stdout": "gnome-calculato\nbash\n"})()
        with patch.object(app_manager.shutil, "which", return_value="/bin/ps"), \
             patch.object(app_manager.subprocess, "run", return_value=fake):
            result = execute_command({"action": "list_running_applications"})
        self.assertEqual(result["data"], ["gnome-calculator"])

    def test_workspace_is_private(self):
        import stat
        target = self.workspace / "private_ws"
        security.ensure_private_workspace(target)
        mode = stat.S_IMODE(target.stat().st_mode)
        self.assertEqual(mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
