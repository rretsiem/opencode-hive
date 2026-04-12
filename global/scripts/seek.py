"""Seek — find the exact definition of any class or function project-wide.

Uses Jedi for scope-aware resolution when available, falls back to pure AST scan.

Usage:
    python3 scripts/seek.py <symbol>
    python3 scripts/seek.py <project_path> <symbol>
    python3 scripts/seek.py src/myproject ConversationAgent
"""

import ast
import os
import sys

SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist", "node_modules", ".ruff_cache", ".pytest_cache"}
NOISE_PARTS = ("/build/", "/dist/", ".venv", "__pycache__")


def _is_noise(path: str) -> bool:
    return any(part in path for part in NOISE_PARTS)


def _iter_python_files(root: str):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


def _ast_find(project_path: str, symbol: str) -> list[tuple[str, int, int, str, str]]:
    """Pure AST scan — zero dependencies."""
    results = []
    for fp in _iter_python_files(project_path):
        try:
            with open(fp, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
                results.append((fp, node.lineno, node.col_offset, "function", f"def {symbol}"))
            elif isinstance(node, ast.ClassDef) and node.name == symbol:
                results.append((fp, node.lineno, node.col_offset, "class", f"class {symbol}"))
    results.sort(key=lambda r: (r[0], r[1]))
    return results


def seek(project_path: str, symbol: str) -> None:
    print(f"Seeking '{symbol}' in '{project_path}'...")
    found = False

    # Try Jedi first (scope-aware, resolves imports)
    try:
        import jedi
        project = jedi.Project(project_path)
        for name in project.search(symbol):
            if not name.is_definition():
                continue
            mp = str(name.module_path)
            if _is_noise(mp):
                continue
            rel = os.path.relpath(mp, os.getcwd())
            print(f"FOUND: {rel}:{name.line}:{name.column}  [{name.type}] {name.description}")
            found = True
    except ImportError:
        pass  # Jedi not installed — fall through to AST
    except Exception as e:
        print(f"Jedi error: {e} — falling back to AST")

    # AST fallback (always runs if Jedi found nothing)
    if not found:
        for fp, line, col, kind, desc in _ast_find(project_path, symbol):
            if _is_noise(fp):
                continue
            rel = os.path.relpath(fp, os.getcwd())
            print(f"FOUND: {rel}:{line}:{col}  [{kind}] {desc}")
            found = True

    if not found:
        print(f"No definition found for '{symbol}'.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/seek.py [project_path] <symbol>")
        sys.exit(1)
    if len(sys.argv) == 2:
        # Default project path: current directory
        proj = os.getcwd()
        seek(proj, sys.argv[1])
    else:
        seek(os.path.abspath(sys.argv[1]), sys.argv[2])
