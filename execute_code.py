import os
import shutil
import tempfile
import subprocess
import time
import logging

logger = logging.getLogger(__name__)

# Docker Sandbox Configuration
DOCKER_PYTHON_IMAGE = os.environ.get("DOCKER_PYTHON_IMAGE", "python:3.10-alpine")
DOCKER_CPP_IMAGE = os.environ.get("DOCKER_CPP_IMAGE", "gcc:latest")
MAX_MEMORY = os.environ.get("EXECUTION_MAX_MEMORY", "256m")
MAX_CPUS = os.environ.get("EXECUTION_MAX_CPUS", "1.0")
DEFAULT_TIMEOUT = float(os.environ.get("EXECUTION_TIMEOUT", "2.0"))


def is_docker_available():
    """Checks if Docker CLI is installed and the Docker daemon is reachable."""
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3
        )
        return res.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return False


def execute_code(source_code, input_data, language, timeout=DEFAULT_TIMEOUT, use_docker=None):
    """
    Executes source code either inside a sandboxed Docker container or via host fallback.
    Returns tuple: (status_string, output_or_error_message, execution_time_in_seconds)
    """
    if use_docker is None:
        use_docker_env = os.environ.get("USE_DOCKER", "").lower()
        if use_docker_env in ("true", "1", "yes"):
            use_docker = True
        elif use_docker_env in ("false", "0", "no"):
            use_docker = False
        else:
            use_docker = is_docker_available()

    if use_docker:
        return execute_code_docker(source_code, input_data, language, timeout)
    else:
        return execute_code_host(source_code, input_data, language, timeout)


def execute_code_docker(source_code, input_data, language, timeout=DEFAULT_TIMEOUT):
    """Executes code within an isolated Docker container with CPU, memory, and network constraints."""
    language = language.lower()
    temp_dir = tempfile.mkdtemp(prefix="sandbox_")
    abs_temp_dir = os.path.abspath(temp_dir)

    try:
        if language == "python":
            script_path = os.path.join(temp_dir, "solution.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(source_code)

            cmd = [
                "docker", "run", "--rm", "-i",
                "--network", "none",
                "--memory", MAX_MEMORY,
                "--memory-swap", MAX_MEMORY,
                "--cpus", MAX_CPUS,
                "-v", f"{abs_temp_dir}:/sandbox:ro",
                DOCKER_PYTHON_IMAGE,
                "python", "/sandbox/solution.py"
            ]

            start_time = time.time()
            try:
                result = subprocess.run(
                    cmd,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                execution_time = time.time() - start_time
                if result.returncode != 0:
                    return "RUNTIME_ERROR", result.stderr.strip(), execution_time
                return "OK", result.stdout.strip(), execution_time
            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                return "TIME_LIMIT_EXCEEDED", "", execution_time

        elif language in ("cpp", "c++"):
            cpp_path = os.path.join(temp_dir, "solution.cpp")
            with open(cpp_path, "w", encoding="utf-8") as f:
                f.write(source_code)

            # Compilation Phase inside Docker container
            compile_cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "-v", f"{abs_temp_dir}:/sandbox:rw",
                DOCKER_CPP_IMAGE,
                "g++", "-O2", "/sandbox/solution.cpp", "-o", "/sandbox/solution"
            ]

            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )

            if compile_result.returncode != 0:
                return "COMPILATION_ERROR", compile_result.stderr.strip(), 0.0

            # Execution Phase inside Docker container (read-only mount)
            run_cmd = [
                "docker", "run", "--rm", "-i",
                "--network", "none",
                "--memory", MAX_MEMORY,
                "--memory-swap", MAX_MEMORY,
                "--cpus", MAX_CPUS,
                "-v", f"{abs_temp_dir}:/sandbox:ro",
                DOCKER_CPP_IMAGE,
                "/sandbox/solution"
            ]

            start_time = time.time()
            try:
                run_result = subprocess.run(
                    run_cmd,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                execution_time = time.time() - start_time
                if run_result.returncode != 0:
                    return "RUNTIME_ERROR", run_result.stderr.strip(), execution_time
                return "OK", run_result.stdout.strip(), execution_time
            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                return "TIME_LIMIT_EXCEEDED", "", execution_time
        else:
            return "RUNTIME_ERROR", f"Unsupported language: {language}", 0.0

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def execute_code_host(source_code, input_data, language, timeout=DEFAULT_TIMEOUT):
    """Fallback execution directly on host OS system."""
    language = language.lower()

    if language == 'python':
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        )
        temp_file.write(source_code)
        temp_file.close()
        file_path = temp_file.name
        try:
            start_time = time.time()
            result = subprocess.run(
                ['python', file_path],
                capture_output=True,
                text=True,
                input=input_data,
                timeout=timeout
            )
            execution_time = time.time() - start_time
            if result.returncode != 0:
                return "RUNTIME_ERROR", result.stderr.strip(), execution_time
            return "OK", result.stdout.strip(), execution_time
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return "TIME_LIMIT_EXCEEDED", "", execution_time
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    elif language in ('cpp', 'c++'):
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.cpp',
            delete=False,
            encoding='utf-8'
        )
        temp_file.write(source_code)
        temp_file.close()
        file_path = temp_file.name
        binary_path = file_path.replace(".cpp", "")
        if os.name == "nt":
            binary_exec = binary_path + ".exe"
        else:
            binary_exec = binary_path

        try:
            compile_result = subprocess.run(
                ['g++', file_path, '-o', binary_exec],
                capture_output=True,
                text=True,
            )
            if compile_result.returncode != 0:
                return "COMPILATION_ERROR", compile_result.stderr.strip(), 0.0

            start_time = time.time()
            run_result = subprocess.run(
                [binary_exec],
                capture_output=True,
                text=True,
                input=input_data,
                timeout=timeout
            )
            execution_time = time.time() - start_time
            if run_result.returncode != 0:
                return "RUNTIME_ERROR", run_result.stderr.strip(), execution_time
            return "OK", run_result.stdout.strip(), execution_time
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return "TIME_LIMIT_EXCEEDED", "", execution_time
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(binary_exec):
                os.remove(binary_exec)
    else:
        return "RUNTIME_ERROR", f"Unsupported language: {language}", 0.0