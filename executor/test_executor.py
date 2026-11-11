import unittest
from command_executor.executor import execute_command
from command_executor.security import WORKSPACE

class ExecutorTests(unittest.TestCase):
    def test_unknown_action(self):
        result = execute_command({"action": "do_magic"})
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "unsupported_action")

    def test_raw_shell_is_rejected(self):
        result = execute_command({"action": "open_application", "target": "firefox", "command": "rm -rf /"})
        self.assertFalse(result["success"])

    def test_create_and_read_file(self):
        name = "executor_test_file.txt"
        created = execute_command({"action": "create_file", "path": name, "content": "hello"})
        self.assertTrue(created["success"])
        read = execute_command({"action": "read_file", "path": name})
        self.assertEqual(read["data"], "hello")
        (WORKSPACE / name).unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
