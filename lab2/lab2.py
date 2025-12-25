from __future__ import annotations
from pathlib import Path
from core.parse import parse_expression
from core.parallel_form import build_parallel_form
from viz.draw_tree import draw_tree

OUT_DIR = Path(__file__).parent / "out"

def run(expr: str) -> None:
    ast = parse_expression(expr)
    parallel = build_parallel_form(ast)
    draw_tree(ast, f"AST: {expr}", OUT_DIR / "lab2_ast.png")
    draw_tree(parallel, f"Parallel form: {expr}", OUT_DIR / "lab2_parallel.png")

def main() -> None:
    expr = "(A+B)+C/D+G+(K/L+M+N)"
    run(expr)

if __name__ == "__main__":
    main()
