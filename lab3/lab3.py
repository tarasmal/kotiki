from core.parse import parse_expression
from core.parallel_form import build_parallel_form
from core.equivalence import assoc_generate, to_infix

def main() -> None:
    expr = "(A+B+C)*(D+E)+F*(G+H+I)"
    max_results = 200

    ast = parse_expression(expr)
    base = build_parallel_form(ast)

    forms = assoc_generate(base, max_results=max_results)

    print("LR3 (Associativity)")
    print(f"Input: {expr}")
    print(f"Base:  {to_infix(base)}")
    print(f"Count: {len(forms)}")
    print()

    for i, f in enumerate(forms, start=1):
        print(f"{i}. {to_infix(f)}")

if __name__ == "__main__":
    main()
