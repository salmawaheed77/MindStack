"""Compatibility tests for Linux operations through MindStack's Executor.

All Linux/computer operations are implemented in executor/. There is no
separate linux_ops package. Run from the project root:
    python3 -m unittest tests.test_linux_ops -v
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from executor import security
from executor.executor import execute_command, get_supported_actions


class ExecutorFileOperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name).resolve()
        self.workspace_patch = patch.object(security, "WORKSPACE", self.workspace)
        self.workspace_patch.start()

    def tearDown(self):
        self.workspace_patch.stop()
        self.temp_dir.cleanup()

    def test_create_file_and_list(self):
        created = execute_command({
            "action": "create_file",
            "path": "test_folder/first.txt",
            "content": "MindStack test",
        })
        self.assertTrue(created["success"], created)

        listed = execute_command({"action": "list_files", "folder": "test_folder"})
        self.assertTrue(listed["success"], listed)
        self.assertIn("first.txt", [item["name"] for item in listed["data"]])

    def test_read_created_file(self):
        execute_command({"action": "create_file", "path": "notes.txt", "content": "hello"})
        result = execute_command({"action": "read_file", "path": "notes.txt"})
        self.assertTrue(result["success"], result)
        self.assertEqual(result["data"], "hello")

    def test_rename_file(self):
        execute_command({"action": "create_file", "path": "old.txt", "content": "x"})
        result = execute_command({
            "action": "rename_file", "path": "old.txt", "new_name": "new.txt"
        })
        self.assertTrue(result["success"], result)
        self.assertTrue((self.workspace / "new.txt").is_file())

    def test_delete_requires_confirmation(self):
        execute_command({"action": "create_file", "path": "remove.txt", "content": "x"})
        result = execute_command({"action": "delete_file", "path": "remove.txt"})
        self.assertEqual(result["error"], "confirmation_required")
        self.assertTrue((self.workspace / "remove.txt").exists())

    def test_delete_after_confirmation(self):
        execute_command({"action": "create_file", "path": "remove.txt", "content": "x"})
        result = execute_command(
            {"action": "delete_file", "path": "remove.txt"}, confirmed=True
        )
        self.assertTrue(result["success"], result)
        self.assertFalse((self.workspace / "remove.txt").exists())

    def test_path_outside_workspace_is_rejected(self):
        result = execute_command({
            "action": "create_file", "path": "../outside.txt", "content": "no"
        })
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "permission_denied")


class ExecutorSystemTests(unittest.TestCase):
    def test_system_actions_are_registered(self):
        actions = get_supported_actions()
        for action in ("get_cpu_usage", "get_memory_usage", "get_disk_usage",
                       "get_system_info", "get_processes"):
            with self.subTest(action=action):
                self.assertIn(action, actions)

    def test_system_info_action_returns_executor_result_shape(self):
        # Avoid depending on the host's real system configuration.
        fake_uname = type("Uname", (), {
            "sysname": "Linux", "nodename": "test-host",
            "release": "test-release", "machine": "x86_64"
        })()
        with patch("executor.system_manager.os.uname", return_value=fake_uname):
            result = execute_command({"action": "get_system_info"})
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result.get("success"), bool)


class ExecutorValidationTests(unittest.TestCase):
    def test_unknown_action_is_rejected(self):
        result = execute_command({"action": "not_a_real_action"})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "unsupported_action")

    def test_raw_shell_command_is_not_accepted(self):
        result = execute_command({
            "action": "open_application",
            "target": "firefox",
            "command": "rm -rf /",
        })
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "permission_denied")


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
