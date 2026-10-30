"""Print the length in lines of a function, from its def line to its last line.

    uv run python tools/function_length.py src/pachaplan/planning.py unpaid_invoices

The count includes the docstring, comments and blank lines inside the body, and the
decorators if there are any. Exits 1 when the function is not found.
"""

import ast
import sys


def function_length(path, name):
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            first = min([node.lineno] + [d.lineno for d in node.decorator_list])
            return node.end_lineno - first + 1
    return None


def main(argv):
    if len(argv) != 3:
        print(f"usage: {argv[0]} FILE FUNCTION", file=sys.stderr)
        return 2
    length = function_length(argv[1], argv[2])
    if length is None:
        print(f"{argv[2]}: not found in {argv[1]}", file=sys.stderr)
        return 1
    print(f"{argv[2]}: {length} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
