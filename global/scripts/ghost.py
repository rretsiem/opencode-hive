"""Ghost — dead code hunter.

Scans a file for functions or classes that are never used anywhere else in the project.
Uses git grep for fast scanning (no external dependencies).

Usage:
    python3 scripts/ghost.py <file_to_check> [project_root]
    python3 scripts/ghost.py src/myproject/tools/weather.py src/myproject
"""

import ast
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_definitions(file_path: str) -> list[tuple[str, int]]:
    """Parse file to find top-level function and class definitions."""
    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        print(f"Error parsing file: {e}")
        return []
    return [
        (node.name, node.lineno)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def check_usage(symbol: str, source_file: str, project_root: str) -> tuple[str, int, list[str]]:
    """Check if a symbol is used outside of its source file."""
    try:
        result = subprocess.run(
            ["git", "grep", "-l", symbol, project_root],
            capture_output=True, text=True, cwd=project_root,
        )
        potential_files = result.stdout.splitlines()
    except Exception:
        result = subprocess.run(
            ["grep", "-rl", symbol, project_root],
            capture_output=True, text=True,
        )
        potential_files = result.stdout.splitlines()

    candidates = [
        f for f in potential_files
        if os.path.abspath(f) != os.path.abspath(source_file) and f.endswith(".py")
    ]
    return (symbol, len(candidates), candidates)


def hunt_ghosts(file_path: str, project_root: str) -> None:
    """Find potentially dead code in a file."""
    print(f"Hunting ghosts in {file_path}...\n")
    definitions = get_definitions(file_path)
    if not definitions:
        print("No top-level definitions found.")
        return

    print(f"Found {len(definitions)} definitions. Scanning project...")
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(check_usage, name, file_path, project_root): (name, line)
            for name, line in definitions
        }
        for future in as_completed(futures):
            name, line = futures[future]
            _, count, files = future.result()
            results.append((name, line, count, files))

    results.sort(key=lambda x: x[1])
    print(f"{'LINE':<6} {'SYMBOL':<40} {'STATUS':<10} {'FILES'}")
    print("-" * 80)

    unused_count = 0
    for name, line, count, files in results:
        status = "USED" if count > 0 else "UNUSED"
        file_summary = f"{count} files" if count > 0 else ""
        if 0 < count <= 3:
            file_summary = ", ".join(os.path.basename(f) for f in files)
        print(f"{line:<6} {name:<40} {status:<10} {file_summary}")
        if count == 0:
            unused_count += 1

    print(f"\nSummary: {unused_count} potentially dead symbols found.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/ghost.py <file_to_check> [project_root]")
        sys.exit(1)
    target = os.path.abspath(sys.argv[1])
    root = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    hunt_ghosts(target, root)
