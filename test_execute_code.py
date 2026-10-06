import os
import unittest
from unittest.mock import patch, MagicMock
from execute_code import execute_code, execute_code_host, execute_code_docker, is_docker_available

class TestExecuteCodeHost(unittest.TestCase):
    def test_python_success(self):
        code = "a, b = map(int, input().split())\nprint(a + b)"
        status, output, exec_time = execute_code_host(code, "3 5\n", "python")
        self.assertEqual(status, "OK")
        self.assertEqual(output, "8")
        self.assertGreaterEqual(exec_time, 0)

    def test_python_runtime_error(self):
        code = "print(1 / 0)"
        status, output, exec_time = execute_code_host(code, "", "python")
        self.assertEqual(status, "RUNTIME_ERROR")
        self.assertIn("ZeroDivisionError", output)

    def test_python_timeout(self):
        code = "import time\ntime.sleep(5)"
        status, output, exec_time = execute_code_host(code, "", "python", timeout=0.5)
        self.assertEqual(status, "TIME_LIMIT_EXCEEDED")
        self.assertEqual(output, "")

    def test_cpp_success(self):
        code = """#include <iostream>
using namespace std;
int main() {
    int a, b;
    if (cin >> a >> b) cout << (a + b);
    return 0;
}"""
        status, output, exec_time = execute_code_host(code, "10 20\n", "cpp")
        self.assertEqual(status, "OK")
        self.assertEqual(output, "30")

    def test_cpp_compilation_error(self):
        code = """#include <iostream>
using namespace std;
int main() {
    this_is_syntax_error;
    return 0;
}"""
        status, output, exec_time = execute_code_host(code, "", "cpp")
        self.assertEqual(status, "COMPILATION_ERROR")
        self.assertNotEqual(output, "")

    def test_unsupported_language(self):
        status, output, exec_time = execute_code_host("print(1)", "", "ruby")
        self.assertEqual(status, "RUNTIME_ERROR")
        self.assertIn("Unsupported language", output)


class TestExecuteCodeDockerFlags(unittest.TestCase):
    @patch("subprocess.run")
    def test_docker_python_flags(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "42"
        mock_result.stderr = ""
        mock_run.returncode = 0
        mock_run.return_value = mock_result

        code = "print(42)"
        status, output, exec_time = execute_code_docker(code, "", "python", timeout=2.0)

        self.assertEqual(status, "OK")
        self.assertEqual(output, "42")

        # Verify docker run was invoked with required security flags
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertIn("docker", cmd)
        self.assertIn("run", cmd)
        self.assertIn("--network", cmd)
        self.assertIn("none", cmd)
        self.assertIn("--memory", cmd)
        self.assertIn("--cpus", cmd)
        self.assertTrue(any(":ro" in arg for arg in cmd))

    @patch("subprocess.run")
    def test_docker_cpp_compilation_and_execution_flags(self, mock_run):
        # 1st call for compile, 2nd call for run
        compile_mock = MagicMock(returncode=0, stdout="", stderr="")
        run_mock = MagicMock(returncode=0, stdout="100", stderr="")
        mock_run.side_effect = [compile_mock, run_mock]

        code = "#include<iostream>\nint main(){ std::cout << 100; }"
        status, output, exec_time = execute_code_docker(code, "", "cpp", timeout=2.0)

        self.assertEqual(status, "OK")
        self.assertEqual(output, "100")
        self.assertEqual(mock_run.call_count, 2)

        # Inspect execution call flags (second call)
        run_cmd = mock_run.call_args_list[1][0][0]
        self.assertIn("--network", run_cmd)
        self.assertIn("none", run_cmd)
        self.assertTrue(any(":ro" in arg for arg in run_cmd))


if __name__ == "__main__":
    unittest.main()
