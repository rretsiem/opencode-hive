"""Which Test — maps a source file to its relevant test files.

Finds all test files that reference or import a specific module.

Usage:
    python3 scripts/which_test.py <file_path>
    python3 scripts/which_test.py src/myproject/session/session.py
"""

import os
import subprocess
import sys


def get_relevant_tests(target_file: str, project_root: str | None = None) -> list[str]:
    """Find test files that reference the target file or its symbols."""
    if project_root is None:
        project_root = os.getcwd()
    rel_path = os.path.relpath(target_file, project_root)
    module_name = rel_path.replace(".py", "").replace("/", ".").split(".")[-1]

    test_dir = os.path.join(project_root, "tests")
    if not os.path.exists(test_dir):
        return []

    try:
        result = subprocess.run(
            ["grep", "-ril", module_name, test_dir],
            capture_output=True, text=True,
        )
        return sorted(
            os.path.relpath(f, os.getcwd())
            for f in result.stdout.splitlines()
            if f.endswith(".py")
        )
    except Exception:
        return []


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/which_test.py <file_path>")
        sys.exit(1)
    tests = get_relevant_tests(sys.argv[1])
    if not tests:
        print("No relevant tests found.")
    else:
        print(f"\n--- Relevant Tests ({len(tests)}) ---")
        for t in tests:
            print(t)
