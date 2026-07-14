"""Skeleton — high-density file map by removing method bodies.

Keeps only signatures, docstrings, type hints, and class-level annotations.
Produces a smaller structural view for understanding large files.

Usage:
    python3 scripts/skeleton.py <file_path>
    python3 scripts/skeleton.py src/myproject/models.py
"""

import ast
import os
import sys


class SkeletonTransformer(ast.NodeTransformer):
    """Traverses the AST and keeps only the 'surface' of the code."""

    def visit_FunctionDef(self, node):
        return self._clean_callable(node)

    def visit_AsyncFunctionDef(self, node):
        return self._clean_callable(node)

    def _clean_callable(self, node):
        new_body = []
        docstring = ast.get_docstring(node)
        if docstring:
            new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
        new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))
        node.body = new_body
        return node

    def visit_ClassDef(self, node):
        new_body = []
        docstring = ast.get_docstring(node)
        if docstring:
            new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                new_body.append(self.visit(item))
            elif isinstance(item, ast.AnnAssign):
                new_body.append(item)
        node.body = new_body
        return node


def get_skeleton(file_path: str) -> str:
    if not os.path.exists(file_path):
        return f"# Error: File {file_path} not found."
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        skeleton_tree = SkeletonTransformer().visit(tree)
        ast.fix_missing_locations(skeleton_tree)
        return ast.unparse(skeleton_tree)
    except Exception as e:
        return f"# Error generating skeleton for {file_path}: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/skeleton.py <file_path>")
        sys.exit(1)
    print(f"# Skeleton of {os.path.basename(sys.argv[1])}")
    print("# Logic omitted for brevity (...)\n")
    print(get_skeleton(sys.argv[1]))
