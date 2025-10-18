import time
from .models import TestCase


def run_in_sandbox(sub):
    # FAKE runner: simulate work and mark AC if code contains "return 0" or "print"
    time.sleep(1.0)
    tests = list(
        TestCase.objects.filter(problem=sub.problem).values(
            "id", "input_data", "expected_output", "hidden"
        )
    )
    passed = []
    for t in tests:
        # naive "pass all"
        passed.append(
            {
                "test_id": str(t["id"]),
                "status": "ok",
                "runtime_ms": 10,
                "memory_kb": 1024,
            }
        )
    final = "ac" if ("return 0" in sub.code or "print" in sub.code) else "wa"
    return {"final_status": final, "tests": passed}
