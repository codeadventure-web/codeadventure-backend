import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .models import Submission, TestCase, Problem, Language


# Map Language.key to Docker image & run command
LANGUAGE_CONFIG: Dict[str, Dict[str, Any]] = {
    "python": {
        "image": "codeadventure-python:3.12",
        "source_filename": "main.py",
        "run_cmd": ["python", "main.py"],
    },
    # "cpp": {
    #     "image": "codeadventure-cpp:latest",
    #     "source_filename": "main.cpp",
    #     "compile_cmd": ["g++", "-O2", "-std=c++17", "main.cpp", "-o", "main"],
    #     "run_cmd": ["./main"],
    # },
}


def _run_in_docker(
    code: str,
    language: Language,
    input_data: str,
    time_limit_ms: int,
    memory_limit_mb: int,
) -> Tuple[str, str, int, str]:
    """
    Run a single testcase in Docker.
    Returns (stdout, stderr, exit_code, status_tag).

    status_tag can be:
      "ok"  - program exited with 0, no timeout
      "tle" - time limit exceeded
      "re"  - runtime error / non-zero exit
    """
    lang_key = language.key
    if lang_key not in LANGUAGE_CONFIG:
        return "", f"Language {lang_key} not supported", -1, "re"

    cfg = LANGUAGE_CONFIG[lang_key]
    image = cfg["image"]
    source_filename = cfg["source_filename"]
    run_cmd = cfg["run_cmd"]
    compile_cmd = cfg.get("compile_cmd")

    # Convert limits
    timeout_sec = max(1.0, time_limit_ms / 1000.0)
    memory_limit = f"{memory_limit_mb}m"  # e.g. "256m"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_path = tmp_path / source_filename
        src_path.write_text(code, encoding="utf-8")

        # Optional compile step (e.g. for C++)
        if compile_cmd:
            try:
                compile_result = subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "--network=none",
                        f"--memory={memory_limit}",
                        "--cpus=1",
                        "-v",
                        f"{tmpdir}:/workspace:rw",
                        "-w",
                        "/workspace",
                        image,
                        *compile_cmd,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_sec,
                )
            except subprocess.TimeoutExpired:
                return "", "Compile TLE", -1, "tle"

            if compile_result.returncode != 0:
                # Compile error
                stderr = compile_result.stderr.decode("utf-8", errors="ignore")
                return "", stderr, compile_result.returncode, "re"

        # Run step
        try:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network=none",
                    f"--memory={memory_limit}",
                    "--cpus=1",
                    "--pids-limit=64",
                    "-v",
                    f"{tmpdir}:/workspace:ro",
                    "-w",
                    "/workspace",
                    image,
                    *run_cmd,
                ],
                input=input_data.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired:
            return "", "Time limit exceeded", -1, "tle"

        stdout = result.stdout.decode("utf-8", errors="ignore").strip()
        stderr = result.stderr.decode("utf-8", errors="ignore").strip()
        rc = result.returncode

        if rc != 0:
            return stdout, stderr, rc, "re"
        return stdout, stderr, rc, "ok"


def run_in_sandbox(sub: Submission) -> Dict[str, Any]:
    """
    REAL runner (for supported languages) using Docker.
    - Runs each testcase of the problem
    - Applies per-problem time/memory limits
    - Compares output with expected_output
    """

    problem: Problem = sub.problem
    language: Language = sub.language

    tests = list(TestCase.objects.filter(problem=problem).order_by("created_at"))

    tests_result: List[Dict[str, Any]] = []
    all_passed = True

    for t in tests:
        start = time.time()

        stdout, stderr, rc, exec_status = _run_in_docker(
            code=sub.code,
            language=language,
            input_data=t.input_data,
            time_limit_ms=problem.time_limit_ms,
            memory_limit_mb=problem.memory_limit_mb,
        )

        runtime_ms = int((time.time() - start) * 1000)

        if exec_status == "tle":
            status = "tle"
        elif exec_status == "re":
            status = "re"
        else:
            # Check output
            expected = t.expected_output.strip()
            if stdout.strip() == expected:
                status = "ok"
            else:
                status = "wa"

        if status != "ok":
            all_passed = False

        tests_result.append(
            {
                "test_id": str(t.id),
                "status": status,
                "hidden": t.hidden,
                "runtime_ms": runtime_ms,
                "memory_kb": 0,  # fill from cgroups later
                "stdout": stdout,
                "stderr": stderr,
            }
        )

    final_status = "ac" if all_passed else "wa"

    return {
        "final_status": final_status,
        "tests": tests_result,
        "compile_output": "",
        "stderr": "",
        "message": "Executed in Docker runner.",
    }
