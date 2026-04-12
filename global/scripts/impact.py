"""Impact — blast radius finder for a symbol.

Finds every file that uses a symbol, distinguishing definitions from usages.
Uses Jedi when available for verified analysis, falls back to git grep + AST.

Usage:
    python3 scripts/impact.py <symbol>
    python3 scripts/impact.py <project_path> <symbol>
    python3 scripts/impact.py src/myproject SessionManager
"""

import ast
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

NOISE_PARTS = ("/build/", "/dist/", ".venv", "__pycache__")


def _is_noise(path: str) -> bool:
    return any(part in path for part in NOISE_PARTS)


def _get_candidates(project_path: str, symbol: str) -> list[str]:
    """Fast scan via git grep, fallback to grep."""
    try:
        result = subprocess.run(
            ["git", "grep", "-l", "-I", symbol, project_path],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return [f for f in result.stdout.splitlines() if f.endswith(".py") and not _is_noise(f)]
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["grep", "-rl", symbol, project_path],
            capture_output=True, text=True,
        )
        return [f for f in result.stdout.splitlines() if f.endswith(".py") and not _is_noise(f)]
    except Exception:
        return []


def _analyze_with_jedi(file_path: str, symbol: str) -> list[str]:
    """Jedi-based verified analysis of a single file."""
    import jedi
    results = []
    try:
        script = jedi.Script(path=file_path)
        for name in script.get_names(all_scopes=True, definitions=True, references=True):
            if name.name == symbol:
                tag = "[DEF]" if name.is_definition() else "[USE]"
                context = "<unavailable>"
                try:
                    with open(file_path, encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                        if 0 <= name.line - 1 < len(lines):
                            context = lines[name.line - 1].strip()
                except Exception:
                    pass
                rel = os.path.relpath(file_path, os.getcwd())
                results.append(f"{tag} {rel}:{name.line} -> {context}")
    except Exception:
        pass
    return results


def _analyze_with_ast(file_path: str, symbol: str) -> list[str]:
    """AST + line scan fallback when Jedi is not available."""
    results = []
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
            source = "".join(lines)
    except (OSError, UnicodeDecodeError):
        return []

    rel = os.path.relpath(file_path, os.getcwd())

    # AST for definitions
    try:
        tree = ast.parse(source, filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
                ctx = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                results.append(f"[DEF] {rel}:{node.lineno} -> {ctx}")
            elif isinstance(node, ast.ClassDef) and node.name == symbol:
                ctx = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                results.append(f"[DEF] {rel}:{node.lineno} -> {ctx}")
    except SyntaxError:
        pass

    # Line scan for usages (simple but effective)
    for i, line in enumerate(lines, 1):
        if symbol in line:
            stripped = line.strip()
            # Skip if it's a definition we already found
            if stripped.startswith(("def ", "class ")) and symbol in stripped.split("(")[0]:
                continue
            results.append(f"[USE] {rel}:{i} -> {stripped}")

    return results


def find_impact(project_path: str, symbol: str) -> None:
    print(f"Calculating impact radius for '{symbol}'...")

    candidates = _get_candidates(project_path, symbol)
    if not candidates:
        print("No occurrences found.")
        return

    print(f"Scanning {len(candidates)} candidate files...")

    # Check if Jedi is available
    try:
        import jedi  # noqa: F401
        analyzer = _analyze_with_jedi
    except ImportError:
        analyzer = _analyze_with_ast

    verified = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(analyzer, f, symbol): f for f in candidates}
        for future in as_completed(futures):
            verified.extend(future.result())

    # Definitions first, then by path
    verified.sort(key=lambda x: (0 if "[DEF]" in x else 1, x))

    print(f"\n--- Verified Impact ({len(verified)}) ---")
    for usage in verified:
        print(usage)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/impact.py [project_path] <symbol>")
        sys.exit(1)
    if len(sys.argv) == 2:
        proj = os.getcwd()
        find_impact(proj, sys.argv[1])
    else:
        find_impact(os.path.abspath(sys.argv[1]), sys.argv[2])
