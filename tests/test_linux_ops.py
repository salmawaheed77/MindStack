import shutil
import unittest

from linux_ops import app_ops, file_ops, system_info


class TestFileOps(unittest.TestCase):
    def setUp(self):
        self.folder = "unittest_dir"
        file_ops.create_folder(self.folder)

    def tearDown(self):
        shutil.rmtree(file_ops.WORKSPACE / self.folder, ignore_errors=True)

    def test_create_and_list(self):
        self.assertTrue(file_ops.create_file(f"{self.folder}/a.txt")["ok"])
        result = file_ops.list_files(self.folder)
        self.assertIn("a.txt", result["data"])

    def test_rename(self):
        file_ops.create_file(f"{self.folder}/a.txt")
        result = file_ops.rename_file(f"{self.folder}/a.txt", f"{self.folder}/b.txt")
        self.assertTrue(result["ok"])

    def test_delete_needs_confirmation(self):
        path = f"{self.folder}/a.txt"
        file_ops.create_file(path)
        self.assertFalse(file_ops.delete_file(path)["ok"])
        self.assertTrue(file_ops.delete_file(path, confirmed=True)["ok"])

    def test_outside_workspace_blocked(self):
        self.assertFalse(file_ops.list_files("../..")["ok"])
        self.assertFalse(file_ops.create_file("../outside.txt")["ok"])


class TestSystemInfo(unittest.TestCase):
    def test_usage_has_all_fields(self):
        data = system_info.show_usage()["data"]
        for key in ("cpu_percent", "ram_percent", "disk_percent"):
            self.assertIn(key, data)

    def test_processes_limit(self):
        result = system_info.show_processes(3)
        self.assertTrue(result["ok"])
        self.assertLessEqual(len(result["data"]), 3)


class TestAppOps(unittest.TestCase):
    def test_not_allowed_app_is_rejected(self):
        self.assertFalse(app_ops.open_app("rm")["ok"])
        self.assertFalse(app_ops.close_app("rm")["ok"])


if __name__ == "__main__":
    unittest.main()
