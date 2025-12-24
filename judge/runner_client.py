import subprocess
import tempfile
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .models import Submission, TestCase, Problem, Language

logger = logging.getLogger(__name__)

# Map Language.key to Docker image & commands
LANGUAGE_CONFIG: Dict[str, Dict[str, Any]] = {
    "python": {
        "image": "codeadventure-python:3.12",
        "source_filename": "main.py",
        "run_cmd": ["python3", "main.py"],
    },
    "cpp": {
        "image": "codeadventure-cpp:latest",
        "source_filename": "main.cpp",
        "compile_cmd": ["g++", "-O2", "-std=c++17", "main.cpp", "-o", "main"],
        "run_cmd": ["./main"],
    },
}


class DockerSandbox:
    def __init__(self, language: Language, code: str, memory_limit_mb: int):
        self.language = language
        self.code = code
        self.memory_limit_mb = memory_limit_mb
        self.container_name = f"sandbox-{uuid.uuid4()}"
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmpdir.name)

        # Load config
        self.cfg = LANGUAGE_CONFIG.get(language.key)
        if not self.cfg:
            raise ValueError(f"Language {language.key} not supported")

    def __enter__(self):
        """Start the container in detached mode (sleeping)."""
        source_filename = self.cfg["source_filename"]
        (self.tmp_path / source_filename).write_text(self.code, encoding="utf-8")

        try:
            subprocess.run(
                [
                    "/usr/bin/docker",
                    "run",
                    "--rm",
                    "-d",  # Detached & remove on exit
                    "--name",
                    self.container_name,  # Unique name
                    # "--network=none",  # Allow network for learning
                    f"--memory={self.memory_limit_mb}m",
                    "--cpus=1",
                    # "--pids-limit=64",  # Removed strict PID limit
                    "-v",
                    f"{self.tmpdir.name}:/workspace:rw",
                    "-w",
                    "/workspace",
                    self.cfg["image"],
                    "sleep",
                    "infinity",  # Keep alive command
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return self
        except Exception as e:
            self.tmpdir.cleanup()
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Force kill the container and cleanup temp dir."""
        try:
            subprocess.run(
                ["/usr/bin/docker", "rm", "-f", self.container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            self.tmpdir.cleanup()

    def compile(self) -> Tuple[bool, str]:
        """Runs the compilation command if defined."""
        compile_cmd = self.cfg.get("compile_cmd")
        if not compile_cmd:
            return True, ""  # No compilation needed (e.g. Python)

        # Run compilation via docker exec
        try:
            res = subprocess.run(
                ["/usr/bin/docker", "exec", self.container_name, *compile_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,  # Increased timeout for compilation
            )
            if res.returncode != 0:
                return False, res.stderr.decode("utf-8", errors="ignore")
            return True, ""
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out."

    def run_test_case(
        self, input_data: str, time_limit_ms: int
    ) -> Tuple[str, str, int, str]:
        """
        Runs a single test case using `docker exec`.
        Returns: (stdout, stderr, exit_code, status_tag)
        """
        timeout_sec = time_limit_ms / 1000.0
        run_cmd = self.cfg["run_cmd"]

        try:
            res = subprocess.run(
                ["/usr/bin/docker", "exec", "-i", self.container_name, *run_cmd],
                input=input_data.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_sec,
            )

            rc = res.returncode

            if rc == 137:
                return "", "Memory Limit Exceeded", rc, "mle"

            stdout = res.stdout.decode("utf-8", errors="ignore").strip()[:10000]
            stderr = res.stderr.decode("utf-8", errors="ignore").strip()[:10000]

            if rc != 0:
                return stdout, stderr, rc, "re"

            return stdout, stderr, rc, "ok"

        except subprocess.TimeoutExpired:
            return "", "Time Limit Exceeded", -1, "tle"
        except Exception as e:
            return "", str(e), -1, "re"


def run_in_sandbox(sub: Submission) -> Dict[str, Any]:
    problem: Problem = sub.problem
    tests = list(TestCase.objects.filter(problem=problem).order_by("created_at"))

    # Fail fast if language not supported
    if sub.language.key not in LANGUAGE_CONFIG:
        return {
            "final_status": "re",
            "message": f"Language {sub.language.key} not configured",
            "tests": [],
        }

    tests_result: List[Dict[str, Any]] = []
    final_status = "ac"

    try:
        with DockerSandbox(sub.language, sub.code, problem.memory_limit_mb) as sandbox:
            is_compiled, compile_err = sandbox.compile()
            if not is_compiled:
                return {
                    "final_status": "ce",
                    "compile_output": compile_err,
                    "tests": [],
                    "message": "Compilation failed",
                }

            for t in tests:
                start = time.time()
                stdout, stderr, rc, status = sandbox.run_test_case(
                    t.input_data, problem.time_limit_ms
                )
                runtime_ms = int((time.time() - start) * 1000)

                if status == "ok":
                    if stdout == t.expected_output.strip():
                        status = "ac"
                    else:
                        status = "wa"

                if status != "ac":
                    if final_status == "ac":
                        final_status = status
                    elif final_status == "wa" and status in ["tle", "mle", "re"]:
                        final_status = status

                tests_result.append(
                    {
                        "test_id": str(t.id),
                        "status": status,
                        "hidden": t.hidden,
                        "runtime_ms": runtime_ms,
                        "stdout": stdout,
                        "stderr": stderr,
                    }
                )

    except Exception as e:
        logger.exception("Sandbox error")
        return {"final_status": "re", "message": "System Error: " + str(e), "tests": []}

    return {
        "final_status": final_status,
        "tests": tests_result,
        "compile_output": "",
    }
